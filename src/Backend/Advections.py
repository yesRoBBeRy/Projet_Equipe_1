import numpy as np

from src.Backend.Collisions import Collisions

class Advections:
    def __init__(self, parametres):
        self.parametres = parametres
        self.collisions = Collisions(parametres)

    def calculer_velocite(self):
        f = self.parametres.F
        #bouger les velocites aux cases voisines
        for i, (cx, cy, cz) in enumerate(zip(self.parametres.cxs, self.parametres.cys, self.parametres.czs)):
           f[:, :, :, i] = np.roll(f[:, :, :, i], cx, axis=0)
           f[:, :, :, i] = np.roll(f[:, :, :, i], cy, axis=1)
           f[:, :, :, i] = np.roll(f[:, :, :, i], cz, axis=2)
        self.parametres.F = f

    def appliquer_inverse(self):
        obstacle = self.parametres.obstacle.astype(bool)
        if not np.any(obstacle):
            return

        # changer direction dans les cellules
        f_obstacle = self.parametres.F[obstacle, :].copy()
        self.parametres.F[obstacle, :] = f_obstacle[:, self.parametres.oppose]

    # Variables du fluide
    def calculer_variables_macroscopiques(self):
        f = self.parametres.F
        self.parametres.rho = np.sum(f, axis=3)
        rho_inv = 1.0 / np.maximum(self.parametres.rho, 0.0001)

        # Changer f et mettre lattices
        flat_f = f.reshape(-1, 27)
        self.parametres.ux = (flat_f @ self.parametres.cxs).reshape(f.shape[:3]) * rho_inv
        self.parametres.uy = (flat_f @ self.parametres.cys).reshape(f.shape[:3]) * rho_inv
        self.parametres.uz = (flat_f @ self.parametres.czs).reshape(f.shape[:3]) * rho_inv

        # No-slip
        obstacle = self.parametres.obstacle.astype(bool)
        self.parametres.ux[obstacle] = 0.0
        self.parametres.uy[obstacle] = 0.0
        self.parametres.uz[obstacle] = 0.0

    def mise_a_jour(self):
        # Calcul de la physique du vent et des collisions

        self.calculer_velocite()

        self.parametres.F[0, :, :, :] = self.parametres.F_inlet

        self.appliquer_inverse()

        self.calculer_variables_macroscopiques()

        self.collisions.calculer_collisions()

        self.parametres.grille.valeurs["densite"] = self.parametres.rho
