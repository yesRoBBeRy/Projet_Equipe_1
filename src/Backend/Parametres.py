import numpy as np

from src.Backend.Obstacle import Obstacle


class Parametres:
    NL = 27

    def __init__(self, vx_init, vy_init, vz_init, pression, temperature, grille):
        self.vx_init = vx_init
        self.vy_init = vy_init
        self.vz_init = vz_init
        self.pression = pression
        self.temperature = temperature
        self.grille = grille
        self.tau = 0.6 #viscosite
        self.obstacle = Obstacle(self.grille).masque

        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        self.rho = np.ones((Nx, Ny, Nz))
        self.ux = np.zeros((Nx, Ny, Nz))
        self.uy = np.zeros((Nx, Ny, Nz))
        self.uz = np.zeros((Nx, Ny, Nz))

        self.cxs, self.cys, self.czs, self.poids = self.lattice()
        self.oppose = self.calculer_inverses()
        self.F = self._init_distribution()
        self.F_inlet = self.F[0, :, :, :].copy()

    # lattice

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
        F = np.ones((Nx, Ny, Nz, self.NL))

        # 1. Fill the whole grid with a tiny rightward breeze
        # (index 12 is usually the +X direction in D3Q27)
        F[:, :, :, 12] = 1.05

        # 2. Strong Inlet force at the very left wall
        F[0:2, :, :, 12] = 2.5

        return F

    def calculer_inverses(self): # utiliser pour flipper la vitesse
        oppose = np.zeros(self.NL, dtype=int)
        for i in range(self.NL):
            for j in range(self.NL):
                if (self.cxs[i] == -self.cxs[j] and
                    self.cys[i] == -self.cys[j] and
                    self.czs[i] == -self.czs[j]):
                    oppose[i] = j
        return oppose