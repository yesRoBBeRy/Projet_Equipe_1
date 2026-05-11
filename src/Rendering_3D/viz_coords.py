"""Repère visuel : domaine centré sur (0,0,0), indices LBM inchangés."""

# Fond uniquement du viewport PyVista (ne modifie pas la palette Qt de l’app).
# Fond viewport 3D (proche du BG Qt pour un rendu sombre cohérent)
PLOTTER_VIEW_BG = "#050d1a"


def volume_node_origin(nx: int, ny: int, nz: int) -> tuple[float, float, float]:
    """Origin pour ImageData (nx+1, ny+1, nz+1) points, spacing 1 — boîte [-nx/2, nx/2]."""
    return (-0.5 * nx, -0.5 * ny, -0.5 * nz)


def lattice_field_origin(nx: int, ny: int, nz: int) -> tuple[float, float, float]:
    """Origin pour ImageData (nx, ny, nz) : point (i,j,k) au centre de cellule i+0.5 - nx/2."""
    return (-0.5 * nx + 0.5, -0.5 * ny + 0.5, -0.5 * nz + 0.5)


def streamline_seed_plane_params(ny: int, nz: int) -> dict[str, float]:
    """
    Même géométrie que le plan de graines des lignes de courant (Projection).

    Retourne les bornes en indices grille, les tailles du rectangle (i×j) et
    ``arm_length`` = max(taille Y, taille Z) pour calibrer un repère XYZ.
    """
    y_min = 2.0
    y_max = float(ny - 3)
    z_min = 2.0
    z_max = float(nz - 3)
    inlet_x = 2.0
    i_size = max(1.0, y_max - y_min)
    j_size = max(1.0, z_max - z_min)
    arm_length = max(i_size, j_size)
    return {
        "inlet_x": inlet_x,
        "y_min": y_min,
        "y_max": y_max,
        "z_min": z_min,
        "z_max": z_max,
        "i_size": i_size,
        "j_size": j_size,
        "arm_length": arm_length,
    }


def bring_named_actor_to_front(plotter, name: str) -> None:
    """Replace l’acteur en fin de pile de rendu pour qu’il s’affiche au-dessus des autres."""
    try:
        if name not in plotter.actors:
            return
        act = plotter.actors[name]
        ren = plotter.renderer
        ren.RemoveActor(act)
        ren.AddActor(act)
    except Exception:
        pass
