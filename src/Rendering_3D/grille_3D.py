import pyvista as pv


class Grille3D:
    def __init__(self, grille, plotter):
        densites = grille.valeurs["densite"]

        self.grille = grille

        self.plotter = plotter

        x, y, z = densites.shape

        #Création du volume de la grille 3D
        self.volume = pv.ImageData(
            dimensions=(x + 1, y + 1, z + 1),
            spacing=(1, 1, 1),
            origin=(0, 0, 0)
        )
        #Transfert des valeurs de densité vers les valeurs de chacune des cellules
        self.volume.cell_data["densite"] = densites.flatten(order="F")
        self.volume = self.volume.cell_data_to_point_data()

        self.acteur_volume = None

    def update_scene(self):
        #Logique de mise à jour de l'opacité
        self.volume.cell_data["densite"] = self.grille.valeurs["densite"].flatten(order="F")
        self.volume= self.volume.cell_data_to_point_data()

        self.acteur_volume.GetMapper().SetInputData(self.volume)
        self.acteur_volume.GetMapper().Update()
        self.plotter.render()