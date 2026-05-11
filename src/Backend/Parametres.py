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
        self.tau = 0.6 #viscosite
        # Rempli depuis les meshs de la scène (voir obstacle_from_scene.sync_obstacle_mask_from_scene)
        self.obstacle = np.zeros((self.grille.Nx, self.grille.Ny, self.grille.Nz), dtype=bool)

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

    def appliquer_parametres_fluide(
        self,
        temperature_c: float,
        viscosite_mpa: float,
        pression_kpa: float,
        vitesse_ms: float,
    ) -> None:
        # Met a jour les parametres configurables

        self.temperature = float(temperature_c)
        self.pression = float(pression_kpa)
        self.vx_init = float(vitesse_ms)
        self.vy_init = 0.0
        self.vz_init = 0.0

        vm = max(0.0, min(1000.0, float(viscosite_mpa)))
        self.tau = float(0.52 + (vm / 1000.0) * 0.43)
        self.tau = max(self.tau, 0.50055)
        self.tau *= float(1.0 + 0.002 * max(-5.0, min(40.0, temperature_c)))
        self.tau = min(self.tau, 1.35)

        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        rho0 = 1.0 + (float(pression_kpa) - 101.325) / 2500.0
        self.rho = np.full((Nx, Ny, Nz), rho0, dtype=np.float64)
        self.ux = np.zeros((Nx, Ny, Nz), dtype=np.float64)
        self.uy = np.zeros((Nx, Ny, Nz), dtype=np.float64)
        self.uz = np.zeros((Nx, Ny, Nz), dtype=np.float64)

        self.F = self._init_distribution_parametrable(vitesse_ms)
        self.F_inlet = self.F[0, :, :, :].copy()

    def _init_distribution_parametrable(self, vitesse_ms: float) -> np.ndarray:
        # changer la vitesse
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz
        F = np.ones((Nx, Ny, Nz, self.NL), dtype=np.float64)
        v01 = max(0.0, min(100.0, float(vitesse_ms))) / 100.0
        bulk = 1.0 + 0.12 * v01
        inlet = 1.45 + 1.35 * v01
        F[:, :, :, 12] = bulk
        F[0:2, :, :, 12] = inlet
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