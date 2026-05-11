from PySide6.QtCore import QObject, QTimer, Signal

from src.Rendering_3D.grille_3D import Grille3D
from src.Rendering_3D.viz_coords import (
    PLOTTER_VIEW_BG,
    bring_named_actor_to_front,
    lattice_field_origin,
    streamline_seed_plane_params,
)
import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor


class Scene3D(QObject):
    forme = Signal(object)

    def __init__(self, parent, grille, /):
        super().__init__(parent)
        self.plotter = QtInteractor(parent)
        try:
            self.plotter.disable_shadows()
        except Exception:
            pass

        # Sélection de forme : left_clicking=False pour ne pas prendre le pas sur la
        # souris du trackball (rotation / panoramique « dans le plan » / zoom molette).
        # PyVista : touche « p » puis clic sur une forme pour la sélectionner.
        self.plotter.enable_mesh_picking(
            callback=self.on_pick,
            use_actor=True,
            show_message=False,
            left_clicking=False,
        )

        self.acteurs_mesh = {}
        self.point_og = {}
        self.parametres_formes = {}
        self.pos_current = {}
        self.rot_current = {}  # acteur -> (rx°, ry°, rz°) autour du centre local
        self.pos_max = {}
        self.acteur_current = None
        self._editing_target = None  # acteur dont le contour jaune est affiché (mode édition)
        self._obstacle_revision = 0
        self._obstacle_mask_synced_rev = -1

        self._render_coalesce_timer = QTimer(self)
        self._render_coalesce_timer.setSingleShot(True)
        self._render_coalesce_timer.setInterval(32)
        self._render_coalesce_timer.timeout.connect(self._flush_plotter_render)

        self.grille = grille
        self.x = grille.x
        self.y = grille.y
        self.z = grille.z
        self.dimensions_grille = self.grille.dimensions

        self.grille_3D = Grille3D(self.grille, self.plotter)

        self.grille_3D.acteur_volume = self.plotter.add_volume(
            self.grille_3D.volume,
            opacity="linear",
            cmap="Greys",
            opacity_unit_distance=55,
            shade=False,
            diffuse=1.0,
            specular=0.0,
            specular_power=1.0,
            ambient=1.0,
            show_scalar_bar=False,
        )
        self.grille_3D.acteur_volume.SetPickable(False)
        ren = self.plotter.renderer
        if hasattr(ren, "SetUseShadows"):
            ren.SetUseShadows(False)
        self._apply_uniform_lighting()
        self.plotter.set_background(PLOTTER_VIEW_BG)
        self._install_world_axes_outside_seed_sized()
        self.plotter.show()

    def _install_world_axes_outside_seed_sized(self):
        """
        Repère XYZ hors du domaine (coin min), bras de longueur = taille caractéristique
        du plan de graines des lignes de courant.
        """
        pl = self.plotter
        for name in (
            "world_axis_x",
            "world_axis_y",
            "world_axis_z",
            "world_axis_labels",
        ):
            if name in pl.actors:
                pl.remove_actor(name)

        Nx, Ny, Nz = int(self.grille.Nx), int(self.grille.Ny), int(self.grille.Nz)
        sp = streamline_seed_plane_params(Ny, Nz)
        ox, oy, oz = lattice_field_origin(Nx, Ny, Nz)
        L = float(sp["arm_length"])
        margin = max(2.5, 0.08 * L)
        base = np.array([ox - margin, oy - margin, oz - margin], dtype=float)

        pl.add_mesh(
            pv.Line(base, base + np.array([L, 0.0, 0.0])),
            color="#ff6b6b",
            line_width=3.5,
            name="world_axis_x",
            pickable=False,
            lighting=False,
        )
        pl.add_mesh(
            pv.Line(base, base + np.array([0.0, L, 0.0])),
            color="#69ff94",
            line_width=3.5,
            name="world_axis_y",
            pickable=False,
            lighting=False,
        )
        pl.add_mesh(
            pv.Line(base, base + np.array([0.0, 0.0, L])),
            color="#5ecbff",
            line_width=3.5,
            name="world_axis_z",
            pickable=False,
            lighting=False,
        )

        tips = np.vstack([base + [L, 0.0, 0.0], base + [0.0, L, 0.0], base + [0.0, 0.0, L]])
        try:
            pl.add_point_labels(
                pv.PolyData(tips),
                ["X", "Y", "Z"],
                font_size=12,
                text_color="#e8f4ff",
                show_points=False,
                always_visible=True,
                shape_opacity=0.4,
                pickable=False,
                name="world_axis_labels",
            )
        except Exception:
            pass

    def _flush_plotter_render(self):
        try:
            self.plotter.render()
        except Exception:
            pass

    def _apply_uniform_lighting(self):
        """Un seul headlight + ambiant global pour un rendu homogène dans la scène."""
        pl = self.plotter
        ren = pl.renderer
        try:
            pl.remove_all_lights()
        except Exception:
            pass
        try:
            ren.SetAmbient(0.5, 0.5, 0.5)
        except Exception:
            pass
        try:
            ren.TwoSidedOn()
        except Exception:
            pass
        pl.add_light(pv.Light(light_type="headlight"))

    def add_sphere(self, rayon):
        center_min = (rayon, rayon, rayon)
        mesh = pv.Sphere(center=center_min, radius=rayon)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "sphere", "params": {"rayon": rayon}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)



    def add_cube(self, c):
        center_min = (c/2,c/2,c/2)
        mesh = pv.Cube(center=center_min, x_length=c, y_length=c, z_length=c)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "cube", "params": {"c": c}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)



    def add_cylindre(self, rayon, l):
        center_min = (l/2, rayon, rayon)
        mesh = pv.Cylinder(center=center_min, radius=rayon, height=l)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "cylindre", "params": {"rayon" : rayon, "h": l}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)



    def add_prisme(self, h, l, w):
        center_min = (h/2, l/2, w/2)
        mesh = pv.Cube(center=center_min, x_length=h, y_length=l, z_length=w)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "prisme", "params": {"h": h, "l": l, "w": w}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)



    def add_pyramide(self, h):
        new_mesh = self._creer_pyramide(h)
        acteur = self._enregistrer(new_mesh)
        self.get_bounds(new_mesh, acteur)
        self.parametres_formes[acteur] = {"type": "pyramide", "params": {"h": h}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)

    def add_fleche(self, l, w):
        mesh = self._creer_fleche_mesh(l, w)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "fleche", "params": {"l": l, "w": w}}
        self.acteur_current = acteur
        self.deplacement(0, 0, 0)


    def on_pick(self, acteur):
        # Définir l'acteur (de la mesh) sélectionné
        # Émettre un signal vers main_window.py pour ouvrir le popup des paramètres
        if acteur in self.acteurs_mesh:
            self.acteur_current = acteur
            self.forme.emit(acteur)



    def _enregistrer(self, mesh):
        # Enregister les paramètres de la forme à la création
        acteur = self.plotter.add_mesh(mesh, lighting=False, smooth_shading=False)
        self.acteurs_mesh[acteur] = mesh
        self._obstacle_revision += 1
        self.point_og[acteur] = mesh.points - np.array(mesh.center)
        self.pos_current[acteur] = tuple(mesh.center)
        self.rot_current[acteur] = (0.0, 0.0, 0.0)
        self.plotter.render()
        return acteur

    @staticmethod
    def _mat_euler_xyz_deg(rx: float, ry: float, rz: float) -> np.ndarray:
        """Matrice 3×3 : rotations intrinsèques XYZ (degrés), sans SciPy."""
        ax, ay, az = np.radians(np.asarray([rx, ry, rz], dtype=float))
        cx, sx = np.cos(ax), np.sin(ax)
        cy, sy = np.cos(ay), np.sin(ay)
        cz, sz = np.cos(az), np.sin(az)
        rx_m = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]], dtype=float)
        ry_m = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]], dtype=float)
        rz_m = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]], dtype=float)
        return rz_m @ ry_m @ rx_m

    def appliquer_pose(self, acteur):
        """Recalcule les points du mesh à partir de point_og, rotation (°) et centre."""
        mesh = self.acteurs_mesh[acteur]
        po = self.point_og[acteur]
        cx, cy, cz = self.pos_current[acteur]
        rx, ry, rz = self.rot_current.get(acteur, (0.0, 0.0, 0.0))
        r = self._mat_euler_xyz_deg(rx, ry, rz)
        c = np.array([cx, cy, cz], dtype=float)
        mesh.points[:] = (r @ po.T).T + c
        self._obstacle_revision += 1
        self._render_coalesce_timer.start(32)
        if self._editing_target == acteur:
            self._refresh_editing_highlight_geometry()

    def set_editing_highlight(self, acteur):
        """Contour jaune filaire autour de la forme en cours d’édition (None pour masquer)."""
        if acteur is not None and acteur not in self.acteurs_mesh:
            acteur = None
        self._editing_target = acteur
        self._refresh_editing_highlight_geometry()

    def _refresh_editing_highlight_geometry(self):
        pl = self.plotter
        if "editing_highlight" in pl.actors:
            pl.remove_actor("editing_highlight")
        if self._editing_target is None:
            return
        mesh = self.acteurs_mesh.get(self._editing_target)
        if mesh is None:
            self._editing_target = None
            return
        shell = mesh.copy(deep=True)
        kw = dict(
            name="editing_highlight",
            style="wireframe",
            color="#ffe200",
            line_width=5.0,
            lighting=False,
            pickable=False,
            reset_camera=False,
        )
        try:
            hl = pl.add_mesh(shell, render_lines_as_tubes=True, **kw)
        except Exception:
            hl = pl.add_mesh(shell, **kw)
        self._apply_highlight_draw_settings(hl)
        bring_named_actor_to_front(pl, "editing_highlight")

    @staticmethod
    def _apply_highlight_draw_settings(actor) -> None:
        """Contour opaque + fragment shader : profondeur minimale pour le voir à travers le volume / obstacles."""
        try:
            actor.ForceOpaqueOn()
        except Exception:
            pass
        try:
            actor.prop.opacity = 1.0
            actor.prop.ambient = 1.0
            actor.prop.diffuse = 0.0
            actor.prop.specular = 0.0
        except Exception:
            pass
        # « X-ray » : même géométrie, mais chaque fragment passe le depth test (comme au premier plan).
        try:
            sp = actor.GetShaderProperty()
            sp.ClearAllShaderReplacements()
            sp.AddFragmentShaderReplacement(
                "//VTK::Depth::Impl",
                False,
                "  gl_FragDepth = 0.0;\n",
                False,
            )
        except Exception:
            pass

    def set_rotation(self, rx_deg: float, ry_deg: float, rz_deg: float):
        """Met à jour la rotation (degrés) de l'acteur courant autour de son centre."""
        if self.acteur_current is None:
            return
        acteur = self.acteur_current
        self.rot_current[acteur] = (float(rx_deg), float(ry_deg), float(rz_deg))
        self.appliquer_pose(acteur)

    def deplacement(self, x, y, z):
        if self.acteur_current is None:
            self.acteur_current = None
            return

        bounds = self.pos_max[self.acteur_current]
        x = max(bounds["x"][0], min(x, bounds["x"][1]))
        y = max(bounds["y"][0], min(y, bounds["y"][1]))
        z = max(bounds["z"][0], min(z, bounds["z"][1]))

        self.pos_current[self.acteur_current] = (x, y, z)
        self.appliquer_pose(self.acteur_current)



    def changer_dimensions_dict(self, valeurs:dict):
        self.changer_dimensions(**valeurs)

    def changer_dimensions(self, **kwargs):
        if self.acteur_current is None:
            return

        acteur = self.acteur_current
        params = self.parametres_formes[acteur]
        params["params"].update(kwargs)

        new_mesh = self._creer_mesh(params)
        new_mesh.points -= np.array(new_mesh.center)
        self.acteurs_mesh[acteur].copy_from(new_mesh)
        self.get_bounds(self.acteurs_mesh[acteur], acteur)
        self.point_og[acteur] = self.acteurs_mesh[acteur].points.copy()

        self.get_bounds(self.acteurs_mesh[acteur], acteur)

        bounds = self.pos_max[acteur]
        pos = self.pos_current[acteur]
        x = max(bounds["x"][0], min(pos[0], bounds["x"][1]))
        y = max(bounds["y"][0], min(pos[1], bounds["y"][1]))
        z = max(bounds["z"][0], min(pos[2], bounds["z"][1]))
        self.pos_current[acteur] = (x, y, z)

        self.appliquer_pose(acteur)

    def _creer_mesh(self, params):
        if params["type"] == "sphere":
            rayon = params["params"]["rayon"]
            return pv.Sphere(center=(rayon, rayon, rayon), radius=rayon)
        elif params["type"] == "cube":
            c = params["params"]["c"]
            return pv.Cube(center=(c / 2, c / 2, c / 2), x_length=c, y_length=c, z_length=c)
        elif params["type"] == "cylindre":
            rayon = params["params"]["rayon"]
            l = params["params"]["h"]
            return pv.Cylinder(center=(l / 2, rayon, rayon), radius=rayon, height=l)
        elif params["type"] == "prisme":
            h = params["params"]["h"]
            l = params["params"]["l"]
            w = params["params"]["w"]
            return pv.Cube(center=(h / 2, l / 2, w / 2), x_length=h, y_length=l, z_length=w)
        elif params["type"] == "pyramide":
            h = params["params"]["h"]
            return self._creer_pyramide(h)
        elif params["type"] == "fleche":
            l = params["params"]["l"]
            w = params["params"]["w"]
            return self._creer_fleche_mesh(l, w)
        return None

    @staticmethod
    def _creer_fleche_mesh(l: float, w: float) -> pv.PolyData:
        """
        Flèche le long de +X. `l` = longueur, `w` = épaisseur (rayon relatif).
        L’ancien code passait tip_radius=w et scale=l : cône énorme en Y/Z, pas une flèche.
        """
        l = max(float(l), 0.5)
        w = max(float(w), 0.5)
        tip_length = 0.48
        frac = min(w / max(l, 1e-9), 1.5)
        tip_radius = 0.09 + 0.22 * frac
        shaft_radius = max(0.035, tip_radius * 0.36)
        return pv.Arrow(
            start=(0.0, 0.0, 0.0),
            direction=(1.0, 0.0, 0.0),
            tip_length=tip_length,
            tip_radius=tip_radius,
            shaft_radius=shaft_radius,
            tip_resolution=24,
            shaft_resolution=24,
            scale=l,
        )



    def _creer_pyramide(self, h):
        # Pyramide à base carrée (un seul sommet) — évite les 4 « pics » d’un tétraèdre
        pyr = pv.Pyramid().copy(deep=True)
        b = np.asarray(pyr.bounds, dtype=float)
        dz = max(b[5] - b[4], 1e-9)
        s = float(h) / dz
        pyr = pyr.scale((s, s, s), inplace=False)
        return pyr.extract_surface(algorithm="dataset_surface")



    def get_bounds(self, mesh, acteur):
        bounds = mesh.bounds
        hx = (bounds[1] - bounds[0]) / 2.0
        hy = (bounds[3] - bounds[2]) / 2.0
        hz = (bounds[5] - bounds[4]) / 2.0
        gx = float(self.dimensions_grille[0])
        gy = float(self.dimensions_grille[1])
        gz = float(self.dimensions_grille[2])
        # Domaine centré sur (0,0,0) : demi-boîte [-gx/2, gx/2] moins la demi-extent du mesh
        self.pos_max[acteur] = {
            "x": [-gx / 2 + hx, gx / 2 - hx],
            "y": [-gy / 2 + hy, gy / 2 - hy],
            "z": [-gz / 2 + hz, gz / 2 - hz],
        }

    def supprimer(self, acteur):
        if acteur in self.acteurs_mesh:
            if self._editing_target == acteur:
                self.set_editing_highlight(None)
            self.plotter.remove_actor(acteur)
            del self.acteurs_mesh[acteur]
            del self.parametres_formes[acteur]
            self.point_og.pop(acteur, None)
            self.pos_current.pop(acteur, None)
            self.rot_current.pop(acteur, None)
            self.pos_max.pop(acteur, None)
            if self.acteur_current == acteur:
                self.acteur_current = None
            self._obstacle_revision += 1
            self.plotter.render()



    def add_forme(self, nom_forme, valeurs):
        d = {
            "sphere" : lambda val: self.add_sphere(val["rayon"]),
            "prisme" : lambda val: self.add_prisme(val["h"], val["l"], val["w"]),
            "cube" : lambda val: self.add_cube(val["c"]),
            "cylindre" : lambda val: self.add_cylindre(val["rayon"], val["h"]),
            "pyramide": lambda val: self.add_pyramide(val["h"]),
            "fleche" : lambda val: self.add_fleche(val["l"], val["w"])
        }
        d[nom_forme](valeurs)
        self.acteur_current = list(self.acteurs_mesh)[-1]
        return self.acteur_current
