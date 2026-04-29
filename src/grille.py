import numpy as np

from src.Backend.Advections import Advections
from src.Backend.Parametres import Parametres


class Grille:
    def __init__(self, x, y, z):
        self.Nx = x
        self.Ny = y
        self.Nz = z
        self.dimensions = np.array([self.Nx, self.Ny, self.Nz])

        self.valeurs = {
            "vx": np.zeros((x, y, z)),
            "vy": np.zeros((x, y, z)),
            "vz": np.zeros((x, y, z)),
            "densite": np.ones((x, y, z))
        }
        self.parametres = Parametres(0.0, 0.0, 0.0, 101.4, 20.0, grille=self)
        self.advection = Advections(self.parametres)
        self.fps = 30

    def test_rand(self):
        forme = self.valeurs["densite"].shape
        self.valeurs["densite"][:] = np.random.uniform(0,1,size=forme)

    def update_valeurs(self):
        self.advection.mise_a_jour()