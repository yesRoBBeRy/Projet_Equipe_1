"""Voxelise les meshes de la scène 3D en masque d'obstacle pour le LBM."""

import numpy as np
import pyvista as pv


def _voxelize_mesh_bbox(mesh, n_x: int, n_y: int, n_z: int) -> np.ndarray:
    """Remplit les cellules LBM dont le centre est dans l’AABB du mesh (rapide)."""
    mask = np.zeros((n_x, n_y, n_z), dtype=bool)
    surf = mesh
    if not isinstance(surf, pv.PolyData):
        surf = surf.extract_surface()
    b = surf.bounds
    x0 = max(0, int(np.floor(b[0] - 0.5 + n_x / 2)))
    x1 = min(n_x, int(np.ceil(b[1] - 0.5 + n_x / 2)) + 1)
    y0 = max(0, int(np.floor(b[2] - 0.5 + n_y / 2)))
    y1 = min(n_y, int(np.ceil(b[3] - 0.5 + n_y / 2)) + 1)
    z0 = max(0, int(np.floor(b[4] - 0.5 + n_z / 2)))
    z1 = min(n_z, int(np.ceil(b[5] - 0.5 + n_z / 2)) + 1)
    if x0 < x1 and y0 < y1 and z0 < z1:
        mask[x0:x1, y0:y1, z0:z1] = True
    return mask


def sync_obstacle_mask_from_scene(scene, parametres, fast: bool = False) -> None:
    """
    Met à jour ``parametres.obstacle`` (bool, shape Nx×Ny×Nz) à partir des
    formes présentes dans ``scene.acteurs_mesh`` (même repère que la grille).

    ``fast=True`` : union des boîtes englobantes uniquement (léger, pour les sliders).
    ``fast=False`` : test « intérieur » point par point (lourd, résultat précis).
    """
    grille = scene.grille
    n_x, n_y, n_z = grille.Nx, grille.Ny, grille.Nz
    mask = np.zeros((n_x, n_y, n_z), dtype=bool)

    meshes = getattr(scene, "acteurs_mesh", None) or {}
    if not meshes:
        parametres.obstacle = mask
        scene._obstacle_mask_synced_rev = scene._obstacle_revision
        return

    if fast:
        for mesh in meshes.values():
            mask |= _voxelize_mesh_bbox(mesh, n_x, n_y, n_z)
        parametres.obstacle = mask
        scene._obstacle_mask_synced_rev = scene._obstacle_revision
        return

    ijk = np.indices((n_x, n_y, n_z), dtype=np.float64)
    centers = np.column_stack(
        [
            (ijk[0] + 0.5 - 0.5 * n_x).ravel(),
            (ijk[1] + 0.5 - 0.5 * n_y).ravel(),
            (ijk[2] + 0.5 - 0.5 * n_z).ravel(),
        ]
    )
    cloud = pv.PolyData(centers)

    for mesh in meshes.values():
        surf = mesh
        if not isinstance(surf, pv.PolyData):
            surf = surf.extract_surface()
        try:
            if hasattr(cloud, "select_interior_points"):
                sel = cloud.select_interior_points(surf, check_surface=False)
                inside = np.asarray(sel["selected_points"], dtype=bool).reshape(
                    (n_x, n_y, n_z), order="C"
                )
            else:
                sel = cloud.select_enclosed_points(
                    surf, tolerance=1e-5, check_surface=False
                )
                inside = sel["SelectedPoints"].astype(bool).reshape(
                    (n_x, n_y, n_z), order="C"
                )
            mask |= inside
        except Exception:
            mask |= _voxelize_mesh_bbox(surf, n_x, n_y, n_z)

    parametres.obstacle = mask
    scene._obstacle_mask_synced_rev = scene._obstacle_revision
