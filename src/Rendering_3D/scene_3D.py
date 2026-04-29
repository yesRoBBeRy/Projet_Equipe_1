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
        self.pos_max = {}
        self.acteur_current = None

        self.grille = grille
        self.x = grille.x
        self.y = grille.y
        self.z = grille.z
        self.dimensions_grille = self.grille.dimensions

        self.grille_3D = Grille3D(self.grille, self.plotter)

        self.grille_3D.acteur_volume = self.plotter.add_volume(
            self.grille_3D.volume,
            opacity="linear",
            cmap="Greys"
        )
        self.grille_3D.acteur_volume.SetPickable(False)
        self.plotter.show()

    def add_sphere(self, rayon):
        center_min = (rayon, rayon, rayon)
        mesh = pv.Sphere(center=center_min, radius=rayon)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "sphere", "params": {"rayon": rayon}}



    def add_cube(self, c):
        center_min = (c/2,c/2,c/2)
        mesh = pv.Cube(center=center_min, x_length=c, y_length=c, z_length=c)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "cube", "params": {"c": c}}



    def add_cylindre(self, rayon, l):
        center_min = (l/2, rayon, rayon)
        mesh = pv.Cylinder(center=center_min, radius=rayon, height=l)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "cylindre", "params": {"rayon" : rayon, "h": l}}



    def add_prisme(self, h, l, w):
        center_min = (h/2, l/2, w/2)
        mesh = pv.Cube(center=center_min, x_length=h, y_length=l, z_length=w)
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "prisme", "params": {"h": h, "l": l, "w": w}}



    def add_pyramide(self, h):
        new_mesh = self._creer_pyramide(h)
        acteur = self._enregistrer(new_mesh)
        self.get_bounds(new_mesh, acteur)
        self.parametres_formes[acteur] = {"type": "pyramide", "params": {"h": h}}

    def add_fleche(self, l, w):
        mesh = pv.Arrow(start=(0, 0, 0), scale=l, tip_radius=w, shaft_radius=w/2)
        b = mesh.bounds
        mesh.points -= np.array([b[0], b[2], b[4]])
        acteur = self._enregistrer(mesh)
        self.get_bounds(mesh, acteur)
        self.parametres_formes[acteur] = {"type": "fleche", "params": {"l": l, "w": w}}


    def on_pick(self, acteur):
        # Définir l'acteur (de la mesh) sélectionné
        # Émettre un signal vers main_window.py pour ouvrir le popup des paramètres
        if acteur in self.acteurs_mesh:
            self.acteur_current = acteur
            self.forme.emit(acteur)



    def _enregistrer(self, mesh):
        # Enregister les paramètres de la forme à la création
        acteur = self.plotter.add_mesh(mesh)
        self.acteurs_mesh[acteur] = mesh
        self.point_og[acteur] = mesh.points - np.array(mesh.center)
        self.pos_current[acteur] = tuple(mesh.center)
        self.plotter.render()
        return acteur



    def deplacement(self, x, y, z):
        if self.acteur_current is None:
            self.acteur_current = None
            return
        mesh = self.acteurs_mesh[self.acteur_current]

        bounds = self.pos_max[self.acteur_current]
        x = max(bounds["x"][0], min(x, bounds["x"][1]))
        y = max(bounds["y"][0], min(y, bounds["y"][1]))
        z = max(bounds["z"][0], min(z, bounds["z"][1]))


        #Ajout de (x, y, z) à chaque point de la mesh
        point_origine = self.point_og[self.acteur_current]
        mesh.points[:] = point_origine + (x, y, z)
        self.pos_current[self.acteur_current] = (x, y, z)
        self.plotter.render()



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

        bornes = self.pos_max[acteur]
        if any(bornes[axe][1] < bornes[axe][0] for axe in ["x", "y", "z"]):
            dims = self.dimensions_grille
            half_extents = [
                (self.acteurs_mesh[acteur].bounds[1] - self.acteurs_mesh[acteur].bounds[0]) / 2,
                (self.acteurs_mesh[acteur].bounds[3] - self.acteurs_mesh[acteur].bounds[2]) / 2,
                (self.acteurs_mesh[acteur].bounds[5] - self.acteurs_mesh[acteur].bounds[4]) / 2,
            ]
            facteur = min(float(dims[i]) / (2 * half_extents[i]) for i in range(3) if half_extents[i] > 0)

            for k, v in params["params"].items():
                params["params"][k] = v * facteur

            new_mesh = self._creer_mesh(params)
            new_mesh.points -= np.array(new_mesh.center)
            self.acteurs_mesh[acteur].copy_from(new_mesh)
            self.point_og[acteur] = self.acteurs_mesh[acteur].points.copy()
            self.get_bounds(self.acteurs_mesh[acteur], acteur)

        pos = self.pos_current[acteur]
        bounds = self.pos_max[acteur]
        x = max(bounds["x"][0], min(pos[0], bounds["x"][1]))
        y = max(bounds["y"][0], min(pos[1], bounds["y"][1]))
        z = max(bounds["z"][0], min(pos[2], bounds["z"][1]))
        self.pos_current[acteur] = (x, y, z)

        self.deplacement(x, y, z)

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
            mesh = pv.Arrow(start=(0, 0, 0), scale=l, tip_radius=w, shaft_radius=w / 2)
            b = mesh.bounds
            mesh.points -= np.array([b[0], b[2], b[4]])
            return mesh
        return None



    def _creer_pyramide(self, h):
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
        points += np.array([base, 0, 0])

        faces = np.array([
            [3, 0, 1, 2],
            [3, 0, 1, 3],
            [3, 1, 2, 3],
            [3, 2, 0, 3],
        ])
        return pv.PolyData(points, faces)



    def get_bounds(self, mesh, acteur):
        bounds = mesh.bounds
        x = (bounds[1] - bounds[0])/2
        y = (bounds[3] - bounds[2])/2
        z = (bounds[5] - bounds[4])/2

        x_max = float(self.dimensions_grille[0]) - x
        y_max = float(self.dimensions_grille[1]) - y
        z_max = float(self.dimensions_grille[2]) - z

        self.pos_max[acteur] = {"x" : [x, x_max], "y": [y, y_max], "z" : [z, z_max]}

    def supprimer(self, acteur):
        if acteur in self.acteurs_mesh:
            self.plotter.remove_actor(acteur)
            del self.acteurs_mesh[acteur]
            del self.parametres_formes[acteur]
            self.point_og.pop(acteur, None)
            self.pos_current.pop(acteur, None)
            self.pos_max.pop(acteur, None)
            if self.acteur_current == acteur:
                self.acteur_current = None
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