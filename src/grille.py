import pyvista as pv
import numpy as np

class Grille:
    def __init__(self, x, y, z):

        self.valeurs = {
            "vx" : np.zeros((x,y,z)),
            "vy" : np.zeros((x,y,z)),
            "vz" : np.zeros((x,y,z)),
            "densitee" : np.ones((x,y,z))
        }

        self.mesh = pv.ImageData(
            dimensions=(x,y,z),
            spacing=(1, 1, 1),
            origin=(0, 0, 0)
        )

        for name, arr in self.valeurs.items():
            self.mesh.cell_data[name] = arr.flatten(order="F")