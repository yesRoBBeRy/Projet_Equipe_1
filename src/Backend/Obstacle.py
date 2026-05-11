import numpy as np


class Obstacle:


    def __init__(self, grille):
        self.grille = grille
        self.masque = np.zeros((grille.Nx, grille.Ny, grille.Nz), dtype=bool)