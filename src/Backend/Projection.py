import numpy as np

class Projection:
    def __init__(self, parametres, grille_3D):
        self.parametres = parametres
        self.grille_3D = grille_3D

    def mise_a_jour(self):
        # push latest rho to grille
        self.grille_3D.grille.valeurs["densite"] = self.parametres.rho

        # update the 3D scene
        self.grille_3D.update_scene()

    def afficher_vitesse(self):
        # push velocity magnitude instead of density
        vitesse = np.sqrt(
            self.parametres.ux**2 +
            self.parametres.uy**2 +
            self.parametres.uz**2
        )
        self.grille_3D.grille.valeurs["densite"] = vitesse
        self.grille_3D.update_scene()