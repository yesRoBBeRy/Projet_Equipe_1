import pyvista as pv
import numpy as np


class Grille:
    def __init__(self, x, y, z):
        self.valeurs = {
            "vx": np.zeros((x, y, z)),
            "vy": np.zeros((x, y, z)),
            "vz": np.zeros((x, y, z)),
            "densitee": np.ones((x, y, z))
        }
        self.test_rand()

    def test_rand(self):
        forme = self.valeurs["densitee"].shape
        self.valeurs["densitee"][:] = np.random.uniform(0,1,size=forme)

    def update_valeurs(self):
        self.valeurs["densitee"] *= 0.99