import numpy as np

from src.Backend.Collisions import Collisions

class Advections:
    def __init__(self, parametres):
        self.parametres = parametres
        self.collisions = Collisions(parametres)

    def calculer_velocite(self):
        F = self.parametres.F
        #bouger les velocites aux cases voisines
        for i, (cx, cy, cz) in enumerate(zip(self.parametres.cxs, self.parametres.cys, self.parametres.czs)):
           F[:, :, :, i] = np.roll(F[:, :, :, i], cx, axis=0)
           F[:, :, :, i] = np.roll(F[:, :, :, i], cy, axis=1)
           F[:, :, :, i] = np.roll(F[:, :, :, i], cz, axis=2)
        self.parametres.F = F

    def appliquer_inverse(self):
        obstacle = self.parametres.obstacle.astype(bool)
        if not np.any(obstacle):
            return

        # Bounce-back: reflect each direction into its opposite at solid cells.
        F_obstacle = self.parametres.F[obstacle, :].copy()
        self.parametres.F[obstacle, :] = F_obstacle[:, self.parametres.oppose]

    # Variables du fluide
    def calculer_variables_macroscopiques(self):
        F = self.parametres.F
        self.parametres.rho = np.sum(F, axis=3)
        rho_inv = 1.0 / np.maximum(self.parametres.rho, 0.0001)

        # A direct dot product is often faster than einsum for this specific shape
        # We reshape F to (N_voxels, 27) and dot it with the lattice vectors (27,)
        flat_F = F.reshape(-1, 27)
        self.parametres.ux = (flat_F @ self.parametres.cxs).reshape(F.shape[:3]) * rho_inv
        self.parametres.uy = (flat_F @ self.parametres.cys).reshape(F.shape[:3]) * rho_inv
        self.parametres.uz = (flat_F @ self.parametres.czs).reshape(F.shape[:3]) * rho_inv

        # No-slip in obstacle cells for cleaner obstacle-following streamlines.
        obstacle = self.parametres.obstacle.astype(bool)
        self.parametres.ux[obstacle] = 0.0
        self.parametres.uy[obstacle] = 0.0
        self.parametres.uz[obstacle] = 0.0

    def mise_a_jour(self):
        # 1. Stream (Movement)
        self.calculer_velocite()

        # 2. Force Inlet (The Fan)
        self.parametres.F[0, :, :, :] = self.parametres.F_inlet

        # 3. Obstacle Bounce-Back
        self.appliquer_inverse()

        # 4. NEW: Optimized Macroscopic Variables
        self.calculer_variables_macroscopiques()

        # 5. Collision (Physics)
        self.collisions.calculer_collisions()

        # 6. Push to renderer
        self.parametres.grille.valeurs["densite"] = self.parametres.rho

    def check_stabilite(self):
        if np.isnan(self.parametres.ux).any():
            print("!!! SIMULATION EXPLODED: NaN detected !!!")
            print("Try: 1. Reducing Inlet Speed | 2. Increasing Tau (Viscosity)")
            return False
        return True