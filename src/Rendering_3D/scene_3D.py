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

    def add_sphere(self, rayon):
        sphere = pv.Sphere(
            radius=float(rayon),
            center=self.set_center()
        )

        self.plotter.add_mesh(sphere)
        self.plotter.render()

    def add_cube(self, c):
        cube = pv.Cube(
            x_length=c,
            y_length=c,
            z_length=c,
            center=self.set_center()
        )
        self.plotter.add_mesh(cube)
        self.plotter.render()

    def add_cylindre(self, rayon, l):
        cylinder = pv.Cylinder(
            radius=rayon,
            height=l,
            center=self.set_center()
        )
        self.plotter.add_mesh(cylinder)
        self.plotter.render()

    def add_prisme(self, h, l, w):
        prisme = pv.Cube(
            x_length=h,
            y_length=l,
            z_length=w,
            center=self.set_center()
        )
        self.plotter.add_mesh(prisme)
        self.plotter.render()

    def add_pyramide(self):
        pyramide = pv.examples.cells.Pyramid()
        self.plotter.add_mesh(pyramide)
        self.plotter.render()





    def set_center(self):
        return (
            float(np.random.uniform(0, 50)),
            float(np.random.uniform(0, 50)),
            float(np.random.uniform(0, 100))
        )