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
        F = self.parametres.F
        obstacle = self.parametres.obstacle

        #velocites inversees pour qu'ils bouncent
        bndryF = F[obstacle, :]
        bndryF = bndryF[:, self.parametres.oppose]
        F[obstacle, :] = bndryF

        self.parametres.ux[obstacle] = 0
        self.parametres.uy[obstacle] = 0
        self.parametres.uz[obstacle] = 0

        self.parametres.F = F

    # Variables du fluide
    def calculer_densite(self):
        return np.sum(self.parametres.F, axis=3)

    def calculer_momentum(self):
        F = self.parametres.F
        rho = self.calculer_densite()
        cxs = self.parametres.cxs[np.newaxis, np.newaxis, np.newaxis, :]
        cys = self.parametres.cys[np.newaxis, np.newaxis, np.newaxis, :]
        czs = self.parametres.czs[np.newaxis, np.newaxis, np.newaxis, :]
        ux = np.sum(F * cxs, axis=3) / rho
        uy = np.sum(F * cys, axis=3) / rho
        uz = np.sum(F * czs, axis=3) / rho
        return ux, uy, uz

    def mise_a_jour(self):
        self.calculer_velocite()
        self.appliquer_inverse()

        self.parametres.rho = self.calculer_densite()
        self.parametres.ux, self.parametres.uy, self.parametres.uz = self.calculer_momentum()

        self.collisions.calculer_collisions()

        self.parametres.grille.valeurs["densite"] = self.parametres.rho
        self.parametres.rho = np.maximum(self.calculer_densite(), 0.0001)