import numpy as np


class Collisions:
    #faire les calculs des collisions

    def __init__(self, parametres):
        self.parametres = parametres

    def calculer_equilibrium(self):
        cxs = self.parametres.cxs[np.newaxis, np.newaxis, np.newaxis, :]
        cys = self.parametres.cys[np.newaxis, np.newaxis, np.newaxis, :]
        czs = self.parametres.czs[np.newaxis, np.newaxis, np.newaxis, :]
        rho = self.parametres.rho[:, :, :, np.newaxis]
        ux = self.parametres.ux[:, :, :, np.newaxis]
        uy = self.parametres.uy[:, :, :, np.newaxis]
        uz = self.parametres.uz[:, :, :, np.newaxis]

        udotu = ux ** 2 + uy ** 2 + uz ** 2
        cdotu = cxs * ux + cys * uy + czs * uz

        feq = rho * self.parametres.poids * (1 + 3 * cdotu + 9 / 2 * cdotu ** 2 - 3 / 2 * udotu)
        return feq

    def calculer_collisions(self):
        feq = self.calculer_equilibrium()
        self.parametres.F = self.parametres.F - (1/self.parametres.tau) * (self.parametres.F - feq)
