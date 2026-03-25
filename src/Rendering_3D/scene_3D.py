from PySide6.QtCore import QObject, Signal

from src.Rendering_3D.grille_3D import Grille3D
import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor


class Scene3D(QObject):
    forme = Signal(object)

    def __init__(self, parent, grille, /):
        super().__init__(parent)
        self.plotter = QtInteractor(parent)

        # Permettre à l'utilisateur de sélectionner une forme
        self.plotter.enable_mesh_picking(
            callback=self.on_pick,
            use_actor=True,
            show_message=False,
            left_clicking=True
        )

        self.acteurs_mesh = {}
        self.point_og = {}
        self.parametres_formes = {}
        self.pos_current = {}
        self.acteur_current = None

        self.grille = grille
        self.x = grille.x
        self.y = grille.y
        self.z = grille.z

        self.grille_3D = Grille3D(self.grille, self.plotter)

        self.grille_3D.acteur_volume = self.plotter.add_volume(
            self.grille_3D.volume,
            opacity="linear",
            cmap="Greys"
        )
        self.grille_3D.acteur_volume.SetPickable(False)
        self.plotter.show()

    def add_sphere(self, rayon):
        acteur = self._enregistrer(pv.Sphere(center=(5,5,5), radius=rayon))
        self.parametres_formes[acteur] = {"type": "sphere", "params": {"rayon": rayon}}

    def add_cube(self, c):
        acteur = self._enregistrer(pv.Cube(center=(0,0,0), x_length=c, y_length=c, z_length=c))
        self.parametres_formes[acteur] = {"type": "cube", "params": {"c": c}}

    def add_cylindre(self, rayon, l):
        acteur = self._enregistrer(pv.Cylinder(center=(0,0,0), radius=rayon, height=l))
        self.parametres_formes[acteur] = {"type": "cylindre", "params": {"l": l}}

    def add_prisme(self, h, l, w):
        acteur = self._enregistrer(pv.Cube(center=(0,0,0), x_length=h, y_length=l, z_length=w))
        self.parametres_formes[acteur] = {"type": "prisme", "params": {"h": h, "l": l, "w": w}}

    def add_pyramide(self, h):
        new_mesh = self._creer_pyramide(h, (0,0,0))
        acteur = self._enregistrer(new_mesh)
        self.parametres_formes[acteur] = {"type": "pyramide", "params": {"h": h}}

    def add_fleche(self, l, w):
        acteur = self._enregistrer(pv.Arrow(center=(0, 0, 0), x_length=l, y_length=w))
        self.parametres_formes[acteur] = {"type": "fleche", "params": {"l": l, "w": w}}

    def on_pick(self, acteur):
        # Définir l'acteur (la mesh) sélectionnée
        # Émettre un signal vers main_window.py pour ouvrir la page des paramètres
        if acteur in self.acteurs_mesh:
            self.acteur_current = acteur
            self.forme.emit(acteur)

    def _enregistrer(self, mesh):
        # Enregister les paramètres de la forme à la création
        acteur = self.plotter.add_mesh(mesh)
        self.acteurs_mesh[acteur] = mesh
        self.point_og[acteur] = mesh.points.copy()
        self.pos_current[acteur] = (0,0,0)
        self.plotter.render()
        return acteur

    def deplacement(self, x, y, z):
        if self.acteur_current is None or self.plotter.picked_mesh is None:
            self.acteur_current = None
            return
        mesh = self.acteurs_mesh[self.acteur_current]
        point_origine = self.point_og[self.acteur_current]
        mesh.points[:] = point_origine + (x, y, z)
        self.pos_current[self.acteur_current] = (x, y, z)
        self.plotter.render()

    def changer_dimensions(self, **kwargs):
        if self.acteur_current is None or self.plotter.picked_mesh is None:
            self.acteur_current = None
            return

        acteur = self.acteur_current
        params = self.parametres_formes[acteur]
        params["params"].update(kwargs)

        new_mesh = self._creer_mesh(params)
        self.acteurs_mesh[acteur].copy_from(new_mesh)
        self.point_og[acteur] = self.acteurs_mesh[acteur].points.copy()
        position = self.pos_current[acteur]
        self.deplacement(position[0], position[1], position[2])


    def _creer_mesh(self, params):
        if params["type"] == "sphere":
            rayon = params["params"]["rayon"]
            new_mesh = pv.Sphere(center=(0,0,0), radius=rayon)
            return new_mesh
        elif params["type"] == "cube":
            c = params["params"]["c"]
            new_mesh = pv.Cube(center=(0,0,0), x_length=c, y_length=c, z_length=c)
            return new_mesh
        elif params["type"] == "cylindre":
            rayon = params["params"]["rayon"]
            h = params["params"]["h"]
            return pv.Cylinder(center=(0,0,0), radius=rayon, height=h)
        elif params["type"] == "prisme":
            l = params["params"]["l"]
            w = params["params"]["w"]
            h = params["params"]["h"]
            return pv.Cube(center=(0,0,0), x_length=l, y_length=h, z_length=w)
        elif params["type"] == "pyramide":
            h = params["params"]["h"]
            return self._creer_pyramide(h, (0,0,0))
        elif params["type"] == "fleche":
            l = params["params"]["l"]
            w = params["params"]["w"]
            return pv.Arrow(center=(0,0,0), x_length=l, y_length=w)
        return None

    def _creer_pyramide(self, h, pos):
        # Code généré par claude.ai
        base = h / 2
        base_vertices = np.array([
            [base, 0, 0],
            [-base, 0, 0],
            [0, base * np.sqrt(3), 0],
        ])

        centre_x = base_vertices[:, 0].mean()
        centre_y = base_vertices[:, 1].mean()
        top = np.array([[centre_x, centre_y, h]])

        points = np.vstack([base_vertices, top])
        points += np.array(pos)

        faces = np.array([
            [3, 0, 1, 2],
            [3, 0, 1, 3],
            [3, 1, 2, 3],
            [3, 2, 0, 3],
        ])
        return pv.PolyData(points, faces)
