import numpy as np


class Advection:
    def __init__(self, parametres):
        self.parametres = parametres
        self.rho = parametres.rho

    def calculer_velocite(self):
        F = self.parametres.F
        for it in range(self.parametres.NL):
            print(it)

            for i, cx, cy, cz in zip(range(self.parametres.NL), self.parametres.cxs, self.parametres.cys, self.parametres.czs):
                F[:, :, :, i] = np.roll(F[:, :, i], cx, axis=1)
                F[:, :, i] = np.roll(F[:, :, i], cy, axis=0)
                F[:, :, :, i] = np.roll(F[:, :, i], cz, axis=2)



    def appliquer_inverse(self):
        F = self.parametres.F
        obstacle = self.parametres.obstacle

        bndryF = F[obstacle, :]
        bndryF = bndryF[:, self.parametres.oppose]
        F[obstacle, :] = bndryF

        self.parametres.F = F

    # Variables du fluide
    def calculer_densite(self):
        F = self.parametres.F
        rho = np.sum(F, 3)
        return  rho

    def calculer_momentum(self):
        F = self.parametres.F
        rho = self.calculer_densite()
        ux = np.sum(F * self.parametres.cxs, 3) / rho
        uy = np.sum(F * self.parametres.cys, 3) / rho
        uz = np.sum(F * self.parametres.czs, 3) / rho
        momentumF = [ux, uy, uz]
        return momentumF