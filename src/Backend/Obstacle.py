import numpy as np


class Obstacle:
    """Conservé pour compatibilité; le masque LBM vient des objets de la scène 3D."""

    def __init__(self, grille):
        self.grille = grille
        self.masque = np.zeros((grille.Nx, grille.Ny, grille.Nz), dtype=bool)