from src.Rendering_3D.grille_3D import Grille3D

from pyvistaqt import QtInteractor


class Scene3D:
    def __init__(self, parent, grille):
        self.plotter = QtInteractor(parent)

        self.grille = grille

        self.grille_3D = Grille3D(self.grille, self.plotter)

        self.grille_3D.acteur_volume = self.plotter.add_volume(
            self.grille_3D.volume,
            opacity="linear",
            cmap="Greys"
        )
        self.plotter.show()