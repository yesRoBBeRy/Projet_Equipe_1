import pyvista as pv


class Grille3D:
    def __init__(self, grille, plotter):
        densites = grille.valeurs["densite"]

        self.densitee_max = densites.max()

        self.grille = grille

        self.plotter = plotter

        x, y, z = densites.shape

        self.volume = pv.ImageData(
            dimensions=(x + 1, y + 1, z + 1),
            spacing=(1, 1, 1),
            origin=(0, 0, 0)
        )
        self.volume.cell_data["densite"] = grille.valeurs["densite"].flatten(order="F")
        self.volume = self.volume.cell_data_to_point_data()

        self.acteur_volume = None

    def update_scene(self):
        #Update de l'opacité des cellules de la grille
        self.volume.cell_data["densite"] = self.grille.valeurs["densite"].flatten(order="F")
        self.volume= self.volume.cell_data_to_point_data()

        self.acteur_volume.GetMapper().SetInputData(self.volume)
        self.acteur_volume.GetMapper().Update()
        self.plotter.render()