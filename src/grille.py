import numpy as np


class Grille:
    def __init__(self, x, y, z):
        #Initialisation des listes 3D selon un dictionnaire
        self.valeurs = {
            "vx": np.zeros((x, y, z)),
            "vy": np.zeros((x, y, z)),
            "vz": np.zeros((x, y, z)),
            "densite": np.ones((x, y, z))
        }
        self.test_rand()

    #Méthode test
    def test_rand(self):
        forme = self.valeurs["densite"].shape
        self.valeurs["densite"][:] = np.random.uniform(0,1,size=forme)

    def update_valeurs(self):
        self.valeurs["densite"] *= 0.99