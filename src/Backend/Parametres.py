import numpy as np


class Parametres:
    NL = 27

    def __init__(self, vx_init, vy_init, vz_init, pression, temperature, grille):
        self.vx_init = vx_init
        self.vy_init = vy_init
        self.vz_init = vz_init
        self.pression = pression
        self.temperature = temperature
        self.grille = grille

        self.F = self._init_distribution()
        self.cxs, self.cys, self.czs, self.poids = self.lattice()
        self.obstacle = self.creer_obstacle()

    # LATTICE

    def lattice(self):
        cxs = np.array([ 0,  0,  1,  1,  1,  0, -1, -1, -1,  0,  0,  1,  1,  1,  0, -1, -1, -1,  0,  0,  1,  1,  1,  0, -1, -1, -1])
        cys = np.array([ 0,  1,  1,  0, -1, -1, -1,  0,  1,  0,  1,  1,  0, -1, -1, -1,  0,  1,  0,  1,  1,  0, -1, -1, -1,  0,  1])
        czs = np.array([-1, -1, -1, -1, -1, -1, -1, -1, -1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1,  1,  1,  1,  1,  1,  1,  1])
        poids = np.array([
            2/27, 1/54, 1/216, 1/54, 1/216, 1/54, 1/216, 1/54, 1/216,  # bas
            8/27, 2/27, 1/54,  2/27, 1/54,  2/27, 1/54,  2/27, 1/54,   # milieu
            2/27, 1/54, 1/216, 1/54, 1/216, 1/54, 1/216, 1/54, 1/216,  # haut
        ])
        return cxs, cys, czs, poids

    #  conditions initiales

    def _init_distribution(self):
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        F = np.ones((Nx, Ny, Nz, self.NL)) + 0.01 * np.random.randn(Nx, Ny, Nz, self.NL)
        F[:, :, :, 12] = 2.3  # velocite initiale vers la droite
        return F

    # obstacle

    def distance(self, x1, y1, z1, x2, y2, z2):
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

    def creer_obstacle(self):
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        x, y, z = np.meshgrid(range(Nx), range(Ny), range(Nz), indexing='ij')
        return self.distance(Nx/4, Ny/2, Nz/2, x, y, z) < 13