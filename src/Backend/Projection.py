import numpy as np
import pyvista as pv
from scipy.ndimage import gaussian_filter
from collections import deque

class Projection:
    def __init__(self, parametres, grille_3D):
        self.parametres = parametres
        self.grille_3D = grille_3D
        self.acteur_streamlines = None
        self.frame_count = 0
        self.initialized = False

        # 1. FORCE THE BACKGROUND TO BLACK IMMEDIATELY
        self.grille_3D.plotter.set_background("black")
        pv.global_theme.allow_empty_mesh = True

    def mise_a_jour(self):
        vitesse = self._calculer_vitesse_normalisee()
        self.grille_3D.grille.valeurs["densite"] = vitesse
        self.grille_3D.update_scene()

    def _calculer_vitesse_normalisee(self):
        vitesse = np.sqrt(self.parametres.ux ** 2 + self.parametres.uy ** 2 + self.parametres.uz ** 2)
        vmax = vitesse.max()
        return vitesse / (vmax + 1e-10)

    import numpy as np
    import pyvista as pv
    from scipy.ndimage import gaussian_filter
    from collections import deque

    import numpy as np
    import pyvista as pv
    from scipy.ndimage import gaussian_filter
    from collections import deque

    import numpy as np
    import pyvista as pv
    from scipy.ndimage import gaussian_filter

    def afficher_streamlines(self):
        Nx, Ny, Nz = self.parametres.grille.Nx, self.parametres.grille.Ny, self.parametres.grille.Nz
        plotter = self.grille_3D.plotter

        # 1. CLEAN INPUT DATA
        ux = np.nan_to_num(self.parametres.ux.astype(np.float64))
        uy = np.nan_to_num(self.parametres.uy.astype(np.float64))
        uz = np.nan_to_num(self.parametres.uz.astype(np.float64))

        # 2. SPHERE RADIUS & MAPPING
        cx, cy, cz = Nx // 2, Ny // 2, Nz // 2
        radius = 12

        # Create the distance field
        z_g, y_g, x_g = np.meshgrid(np.arange(Nz), np.arange(Ny), np.arange(Nx), indexing='ij')
        dist = np.sqrt((x_g - cx) ** 2 + (y_g - cy) ** 2 + (z_g - cz) ** 2)

        # 3. ROBUST FLOW MODIFICATION
        # Force a base wind of 0.1 so lines always have a direction
        ux_final = np.abs(ux) + 0.1

        # Use np.where to avoid the IndexError mismatch
        # If inside sphere (dist <= radius), set velocity to 0.
        ux_final = np.where(dist <= radius, 0.0, ux_final)
        uy_final = np.where(dist <= radius, 0.0, uy)
        uz_final = np.where(dist <= radius, 0.0, uz)

        # 4. CREATE VTK GRID
        grid = pv.ImageData(dimensions=(Nx, Ny, Nz), spacing=(1, 1, 1), origin=(0, 0, 0))

        # Flatten using 'F' order to ensure consistency with PyVista's expectations
        grid.point_data["Velocity"] = np.column_stack([
            gaussian_filter(ux_final, sigma=1.0).flatten(order="F"),
            gaussian_filter(uy_final, sigma=1.0).flatten(order="F"),
            gaussian_filter(uz_final, sigma=1.0).flatten(order="F")
        ])

        # 5. SEEDING (8x8 Grid = 64 Lines)
        y_seeds = np.linspace(5, Ny - 5, 8)
        z_seeds = np.linspace(5, Nz - 5, 8)
        yy, zz = np.meshgrid(y_seeds, z_seeds)
        seeds = pv.PolyData(np.column_stack([np.full_like(yy.flatten(), 2), yy.flatten(), zz.flatten()]))

        # 6. INTEGRATION
        streamlines = grid.streamlines_from_source(
            seeds,
            vectors="Velocity",
            max_steps=2000,
            initial_step_length=0.5,
            integration_direction='forward',
            terminal_speed=0.0
        )

        # 7. RENDER
        plotter.remove_actor("streamline_layer")
        if streamlines.n_points > 0:
            # Color by Speed (Magnitude)
            vel_mag = np.linalg.norm(streamlines.point_data["Velocity"], axis=1)
            streamlines.point_data["Speed"] = vel_mag

            plotter.add_mesh(
                streamlines,
                scalars="Speed",
                cmap="turbo",
                line_width=2,
                render_lines_as_tubes=True,
                show_scalar_bar=False,
                name="streamline_layer"
            )

        plotter.render()