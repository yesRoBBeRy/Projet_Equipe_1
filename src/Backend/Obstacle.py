import numpy as np

class Obstacle:
    def __init__(self, grille):
        self.grille = grille
        self.masque = self._creer_obstacle()

    def _creer_obstacle(self):
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        x, y, z = np.meshgrid(range(Nx), range(Ny), range(Nz), indexing='ij')
        dist = np.sqrt((x - Nx/4)**2 + (y - Ny/2)**2 + (z - Nz/2)**2)
        return dist < 13