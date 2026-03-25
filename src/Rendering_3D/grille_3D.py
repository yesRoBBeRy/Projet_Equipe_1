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
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz

        temp = pv.ImageData(
            dimensions=(Nx + 1, Ny + 1, Nz + 1),
            spacing=(1, 1, 1),
            origin=(0, 0, 0)
        )
        temp.cell_data["densite"] = self.grille.valeurs["densite"].flatten(order="F")
        temp = temp.cell_data_to_point_data()

        self.volume.point_data["densite"] = temp.point_data["densite"]
        self.acteur_volume.GetMapper().SetInputData(self.volume)
        self.acteur_volume.GetMapper().Update()
        self.plotter.render()