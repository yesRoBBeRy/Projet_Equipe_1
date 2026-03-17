from src.Rendering_3D.grille_3D import Grille3D
import numpy as np


import pyvista as pv
from pyvistaqt import QtInteractor


class Scene3D:
    def __init__(self, parent, grille):
        self.plotter = QtInteractor(parent)

        self.grille = grille

        self.grille_3D = Grille3D(self.grille, self.plotter)

        self.grille_3D.acteur_volume = self.plotter.add_volume(
            self.grille_3D.volume,
            opacity="linear",
            cmap="Greys"
        )
        self.plotter.show()

    def add_sphere(self):
        sphere = pv.Sphere(
            radius=float(np.random.uniform(0.5, 2.0)),  # Must be a single number
            center=(
                float(np.random.uniform(0, 50)),  # X coordinate
                float(np.random.uniform(0, 50)),  # Y coordinate
                float(np.random.uniform(0, 100))  # Z coordinate
            )
        )

        self.plotter.add_mesh(sphere)
        self.plotter.render()
