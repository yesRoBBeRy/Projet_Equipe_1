import pyvista as pv
import numpy as np
from pyvistaqt import QtInteractor


class Scene3D:
    def __init__(self, parent, grille):
        self.plotter = QtInteractor(parent)

        self.grille = grille

        densitees = self.grille.valeurs["densitee"]

        self.densitee_max = densitees.max()

        x, y, z = densitees.shape

        self.mesh = pv.ImageData(
            dimensions=(x + 1, y + 1, z + 1),
            spacing=(1, 1, 1),
            origin=(0, 0, 0)
        )
        self.mesh.cell_data["densitee"] = grille.valeurs["densitee"].flatten(order="F")
        self.mesh = self.mesh.cell_data_to_point_data()

        self.acteur_volume = self.plotter.add_volume(
            self.mesh,
            opacity="linear",
            cmap="Greys"
        )
        self.plotter.show()

    def update_scene(self):
        self.mesh.cell_data["densitee"] = self.grille.valeurs["densitee"].flatten(order="F")
        self.mesh = self.mesh.cell_data_to_point_data()

        self.acteur_volume.GetMapper().SetInputData(self.mesh)
        self.acteur_volume.GetMapper().Update()
        self.plotter.render()