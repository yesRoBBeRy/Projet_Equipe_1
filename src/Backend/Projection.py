import threading

import numpy as np
import pyvista as pv
from scipy.ndimage import binary_dilation, generate_binary_structure

from PySide6.QtWidgets import QApplication

from src.Rendering_3D.viz_coords import (
    PLOTTER_VIEW_BG,
    bring_named_actor_to_front,
    lattice_field_origin,
    streamline_seed_plane_params,
)

#Conditions pour les streamlines et ne pas voir les streamlines avant d'avoir le final
STREAMLINE_FREEZE_FRAMES = 8
STREAMLINE_SEED_RES = 22
STREAMLINE_WARMUP_STEPS = 120


class Projection:
    def __init__(self, parametres, grille_3d):
        self.parametres = parametres
        self.grille_3D = grille_3d
        self.frame_count = 0
        self._sl_skip = 0
        self._seed_cache = None
        self._seed_signature = None
        self._smoothed_velocity = None
        self._lbm_steps_for_sl = 0
        self._streamline_warmup_active = False
        self._obstacle_mask_cache = None

        pl = self.grille_3D.plotter
        pl.set_background(PLOTTER_VIEW_BG)
        try:
            pl.disable_shadows()
        except Exception:
            pass
        pv.global_theme.allow_empty_mesh = True

    def remove_streamline_layer(self):
        #juste enlever les streamlines
        pl = self.grille_3D.plotter
        if "streamline_layer" in pl.actors:
            pl.remove_actor("streamline_layer")
        self._sl_skip = 0
        self._smoothed_velocity = None
        self.frame_count = 0
        self._streamline_warmup_active = False
        try:
            pl.render()
        except Exception:
            pass

    def clear_streamlines(self):
        # tout enlever
        self.remove_streamline_layer()
        self._lbm_steps_for_sl = 0
        self._obstacle_mask_cache = None
        pl = self.grille_3D.plotter
        if "obstacle_mesh" in pl.actors:
            pl.remove_actor("obstacle_mesh")
        try:
            pl.render()
        except Exception:
            pass

    def record_lbm_step_for_streamlines(self):
        self._lbm_steps_for_sl += 1

    def reset_streamline_warmup(self):
        #Lancer
        self._lbm_steps_for_sl = 0
        self._streamline_warmup_active = True
        self._smoothed_velocity = None
        self.frame_count = 0
        self._sl_skip = 0

    def mise_a_jour(self):
        vitesse = self._calculer_vitesse_normalisee()
        self.grille_3D.grille.valeurs["densite"] = vitesse
        self.grille_3D.update_scene()

    def _calculer_vitesse_normalisee(self):
        vitesse = np.sqrt(self.parametres.ux ** 2 + self.parametres.uy ** 2 + self.parametres.uz ** 2)
        vmax = vitesse.max()
        return vitesse / (vmax + 1e-10)

    def _integrate_streamlines_polydata(self, grid, terminal_speed):
        sl_kw = dict(
            vectors="Velocity",
            integration_direction="forward",
            max_steps=4000,
            initial_step_length=0.2,
            terminal_speed=terminal_speed,
            integrator_type=2,
        )
        out_holder: list = [None]
        err_holder: list = [None]

        def _integrate_worker(work_grid, work_seed):
            try:
                out_holder[0] = work_grid.streamlines_from_source(
                    work_seed,
                    **sl_kw,
                )
            except Exception as e:
                err_holder[0] = e

        work_grid = grid.copy(deep=True)
        work_seed = self._seed_cache.copy(deep=True)
        worker = threading.Thread(
            target=_integrate_worker,
            args=(work_grid, work_seed),
            daemon=True,
        )
        worker.start()
        while worker.is_alive():
            QApplication.processEvents()
            worker.join(timeout=0.04)
        worker.join()
        if err_holder[0] is not None:
            raise err_holder[0]
        return out_holder[0]

    def afficher_streamlines(self):

        if self.frame_count == 0:
            self._smoothed_velocity = None

        nx, ny, nz = self.parametres.grille.Nx, self.parametres.grille.Ny, self.parametres.grille.Nz
        ox, oy, oz = lattice_field_origin(nx, ny, nz)
        plotter = self.grille_3D.plotter

        mask = (
            self.parametres.obstacle.astype(bool)
            if hasattr(self.parametres, "obstacle")
            else np.zeros((nx, ny, nz), dtype=bool)
        )
        # Reconstruire le maillage obstacle que si mask change
        obs_changed = self._obstacle_mask_cache is None or (
            not np.array_equal(mask, self._obstacle_mask_cache)
        )
        if obs_changed:
            self._obstacle_mask_cache = mask.copy()
            if "obstacle_mesh" in plotter.actors:
                plotter.remove_actor("obstacle_mesh")
            if np.any(mask):
                grid_mask = pv.ImageData(
                    dimensions=(nx, ny, nz),
                    spacing=(1, 1, 1),
                    origin=(ox, oy, oz),
                )
                grid_mask.point_data["values"] = mask.astype(np.uint8).flatten(order="F")
                contour = grid_mask.contour([0.5])
                plotter.add_mesh(
                    contour,
                    color="silver",
                    lighting=False,
                    smooth_shading=False,
                    name="obstacle_mesh",
                )
        struct = generate_binary_structure(3, 1)
        mask_vel = (
            binary_dilation(mask, structure=struct, iterations=2)
            if np.any(mask)
            else mask
        )

        ux = np.nan_to_num(self.parametres.ux.astype(np.float32))
        uy = np.nan_to_num(self.parametres.uy.astype(np.float32))
        uz = np.nan_to_num(self.parametres.uz.astype(np.float32))
        ux[mask_vel] = 0.0
        uy[mask_vel] = 0.0
        uz[mask_vel] = 0.0

        if self._smoothed_velocity is None:
            self._smoothed_velocity = (ux.copy(), uy.copy(), uz.copy())
        else:
            alpha = 0.55
            pux, puy, puz = self._smoothed_velocity
            ux = (1.0 - alpha) * pux + alpha * ux
            uy = (1.0 - alpha) * puy + alpha * uy
            uz = (1.0 - alpha) * puz + alpha * uz
            self._smoothed_velocity = (ux.copy(), uy.copy(), uz.copy())

        v_mag = np.sqrt(ux ** 2 + uy ** 2 + uz ** 2)
        local_max_speed = float(np.max(v_mag))
        if local_max_speed < 1e-8:
            self.frame_count += 1
            bring_named_actor_to_front(plotter, "editing_highlight")
            plotter.render()
            return

        # Pas de lignes jusqua stabilisation.
        if (
            self._streamline_warmup_active
            and self._lbm_steps_for_sl < STREAMLINE_WARMUP_STEPS
        ):
            if "streamline_layer" in plotter.actors:
                plotter.remove_actor("streamline_layer")
            bring_named_actor_to_front(plotter, "editing_highlight")
            plotter.render()
            return

        if "streamline_layer" in plotter.actors:
            self._sl_skip += 1
            if self._sl_skip < STREAMLINE_FREEZE_FRAMES:
                self.frame_count += 1
                bring_named_actor_to_front(plotter, "editing_highlight")
                plotter.render()
                return
        self._sl_skip = 0

        grid = pv.ImageData(
            dimensions=(nx, ny, nz),
            spacing=(1, 1, 1),
            origin=(ox, oy, oz),
        )
        vectors = np.empty((grid.n_points, 3), dtype=np.float32)
        vectors[:, 0] = ux.flatten(order="F")
        vectors[:, 1] = uy.flatten(order="F")
        vectors[:, 2] = uz.flatten(order="F")
        grid.point_data["Velocity"] = vectors

        sp = streamline_seed_plane_params(ny, nz)
        y_min = sp["y_min"]
        y_max = sp["y_max"]
        z_min = sp["z_min"]
        z_max = sp["z_max"]
        inlet_x = sp["inlet_x"]

        seed_signature = (
            nx,
            ny,
            nz,
            inlet_x,
            round(y_min, 2),
            round(y_max, 2),
            round(z_min, 2),
            round(z_max, 2),
            STREAMLINE_SEED_RES,
        )
        if self._seed_cache is None or self._seed_signature != seed_signature:
            sx = inlet_x + ox
            sy = 0.5 * (y_min + y_max) + oy
            sz = 0.5 * (z_min + z_max) + oz
            self._seed_cache = pv.Plane(
                center=(sx, sy, sz),
                direction=(1, 0, 0),
                i_size=sp["i_size"],
                j_size=sp["j_size"],
                i_resolution=STREAMLINE_SEED_RES,
                j_resolution=STREAMLINE_SEED_RES,
            )
            self._seed_signature = seed_signature

        if self._seed_cache.n_points == 0:
            self.frame_count += 1
            bring_named_actor_to_front(plotter, "editing_highlight")
            plotter.render()
            return

        terminal_speed = max(local_max_speed * 1e-4, 1e-9)
        candidate = self._integrate_streamlines_polydata(grid, terminal_speed)
        streamlines = candidate
        if streamlines is not None and streamlines.n_points > 0:
            if streamlines.n_cells > 800:
                keep_ids = np.arange(0, streamlines.n_cells, 2, dtype=np.int64)
                streamlines = streamlines.extract_cells(keep_ids)
            streamlines.point_data["Speed"] = np.linalg.norm(
                streamlines.point_data["Velocity"], axis=1
            )
            if "streamline_layer" in plotter.actors:
                plotter.remove_actor("streamline_layer")
            actor = plotter.add_mesh(
                streamlines,
                scalars="Speed",
                cmap="turbo",
                line_width=2.5,
                render_lines_as_tubes=False,
                lighting=False,
                name="streamline_layer",
                show_scalar_bar=False,
            )
            try:
                actor.prop.lighting = False
            except Exception:
                pass
        else:
            if "streamline_layer" in plotter.actors:
                plotter.remove_actor("streamline_layer")
        self.frame_count += 1
        bring_named_actor_to_front(plotter, "editing_highlight")
        plotter.render()
