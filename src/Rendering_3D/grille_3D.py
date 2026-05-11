import numpy as np
import pyvista as pv

from src.Rendering_3D.viz_coords import bring_named_actor_to_front, volume_node_origin


def _densite_pour_volume(rho_pt: np.ndarray) -> np.ndarray:
    """
    Étire le contraste du scalaire affiché dans le volume (ρ LBM ~ 1 partout).
    Sans cela, la carte « Greys » donne un bloc uniforme sombre dès que la sim tourne.
    """
    r = np.asarray(rho_pt, dtype=np.float32).ravel()
    if r.size == 0:
        return rho_pt.astype(np.float32)
    lo, hi = float(np.percentile(r, 4.0)), float(np.percentile(r, 96.0))
    if hi <= lo + 1e-8:
        out = np.full_like(rho_pt, 0.55, dtype=np.float32)
        return out
    t = np.clip((rho_pt.astype(np.float32) - lo) / (hi - lo), 0.0, 1.0)
    return (0.14 + 0.86 * t).astype(np.float32)


class Grille3D:
    def __init__(self, grille, plotter):
        densites = grille.valeurs["densite"]

        self.densitee_max = densites.max()

        self.grille = grille

        self.plotter = plotter

        x, y, z = densites.shape
        ox, oy, oz = volume_node_origin(x, y, z)

        self.volume = pv.ImageData(
            dimensions=(x + 1, y + 1, z + 1),
            spacing=(1, 1, 1),
            origin=(ox, oy, oz),
        )
        self.volume.cell_data["densite"] = grille.valeurs["densite"].flatten(order="F")
        self.volume = self.volume.cell_data_to_point_data()

        self.acteur_volume = None

    def update_scene(self):
        Nx, Ny, Nz = self.grille.Nx, self.grille.Ny, self.grille.Nz

        ox, oy, oz = volume_node_origin(Nx, Ny, Nz)
        temp = pv.ImageData(
            dimensions=(Nx + 1, Ny + 1, Nz + 1),
            spacing=(1, 1, 1),
            origin=(ox, oy, oz),
        )
        temp.cell_data["densite"] = self.grille.valeurs["densite"].flatten(order="F")
        temp = temp.cell_data_to_point_data()

        rho_pt = np.asarray(temp.point_data["densite"], dtype=np.float32)
        self.volume.point_data["densite"] = _densite_pour_volume(rho_pt)
        self.acteur_volume.GetMapper().SetInputData(self.volume)
        self.acteur_volume.GetMapper().Update()
        bring_named_actor_to_front(self.plotter, "editing_highlight")
        self.plotter.render()
