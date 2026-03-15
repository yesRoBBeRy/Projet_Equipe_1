class Collisions:

    def __init__(self, parametres):
        self.parametres = parametres

    def calculer_collisions(self):
        obstacle = self.parametres.obstacle
        bndryF = F[obstacle, :, :]
        bndryF = bndryF[:, [0, 5, 6, 7, 8, 1, 2, 3 ,4]]

    def verif(self):
        pass
