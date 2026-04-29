import numpy as np
import pyvista as pv
from scipy.ndimage import gaussian_filter

class Projection:
    def __init__(self, parametres, grille_3D):
        self.parametres = parametres
        self.grille_3D = grille_3D
        self.acteur_streamlines = None
        self.frame_count = 0
        self.initialized = False
        self._seed_cache = None
        self._seed_signature = None
        self._smoothed_velocity = None
        self._frozen_streamlines = None
        self._frozen_max_time = 0.0
        self._reveal_time = 0.0
        self._streamlines_ready = False
        self._freeze_wait_frames = 0

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

    def afficher_streamlines(self):
        if self.frame_count == 0:
            # Restart a clean "grow smoothly" animation when Run is pressed.
            self._frozen_streamlines = None
            self._frozen_max_time = 0.0
            self._reveal_time = 0.0
            self._streamlines_ready = False
            self._freeze_wait_frames = 0

        # 1. SETUP & DIMENSIONS
        Nx, Ny, Nz = self.parametres.grille.Nx, self.parametres.grille.Ny, self.parametres.grille.Nz
        plotter = self.grille_3D.plotter

        # 2. OBSTACLE BOUNDARY
        plotter.remove_actor("streamline_layer")
        mask = self.parametres.obstacle.astype(bool) if hasattr(self.parametres, "obstacle") else np.zeros((Nx, Ny, Nz), dtype=bool)
        if "obstacle_mesh" not in plotter.actors and np.any(mask):
            grid_mask = pv.ImageData(dimensions=(Nx, Ny, Nz))
            grid_mask.point_data["values"] = mask.astype(np.uint8).flatten(order="F")
            contour = grid_mask.contour([0.5])
            plotter.add_mesh(contour, color="silver", name="obstacle_mesh")

        # 3. EXTRACT VELOCITY (Lattice Units)
        ux = gaussian_filter(np.nan_to_num(self.parametres.ux.astype(np.float32)), sigma=0.5)
        uy = gaussian_filter(np.nan_to_num(self.parametres.uy.astype(np.float32)), sigma=0.5)
        uz = gaussian_filter(np.nan_to_num(self.parametres.uz.astype(np.float32)), sigma=0.5)
        ux[mask] = 0.0
        uy[mask] = 0.0
        uz[mask] = 0.0

        # Temporal smoothing reduces visual jitter between frames.
        if self._smoothed_velocity is None:
            self._smoothed_velocity = (ux.copy(), uy.copy(), uz.copy())
        else:
            alpha = 0.6  # react faster to current flow, less "stuck" inertia
            pux, puy, puz = self._smoothed_velocity
            ux = (1.0 - alpha) * pux + alpha * ux
            uy = (1.0 - alpha) * puy + alpha * uy
            uz = (1.0 - alpha) * puz + alpha * uz
            self._smoothed_velocity = (ux.copy(), uy.copy(), uz.copy())

        # DEBUG CHECK: See if the physics is actually moving
        v_mag = np.sqrt(ux ** 2 + uy ** 2 + uz ** 2)
        if np.max(v_mag) < 1e-10:
            print("CRITICAL: LBM Velocity is zero. Lines cannot be drawn.")
            return

        # 4. DATA ALIGNMENT (The 'C' vs 'F' Order)
        # Portinari's cartesian grid mapping
        grid = pv.ImageData(dimensions=(Nx, Ny, Nz), spacing=(1, 1, 1))

        # We must match the numpy memory layout to the PyVista grid
        vectors = np.empty((grid.n_points, 3), dtype=np.float32)
        vectors[:, 0] = ux.flatten(order="F")
        vectors[:, 1] = uy.flatten(order="F")
        vectors[:, 2] = uz.flatten(order="F")
        grid.point_data["Velocity"] = vectors

        local_max_speed = float(np.max(v_mag))
        # Avoid noisy startup artifacts before a real flow field is established.
        if local_max_speed < 1e-5:
            plotter.render()
            return

        # 5. SEEDING
        # Use the full inlet plane so frozen lines can reach the true final state.
        y_min = 2.0
        y_max = float(Ny - 3)
        z_min = 2.0
        z_max = float(Nz - 3)
        # Inlet is enforced at x=0 in Advections; trace forward from left side.
        inlet_x = 2

        seed_signature = (
            Nx, Ny, Nz, inlet_x,
            round(y_min, 2), round(y_max, 2),
            round(z_min, 2), round(z_max, 2)
        )
        if self._seed_cache is None or self._seed_signature != seed_signature:
            self._seed_cache = pv.Plane(
                center=(inlet_x, 0.5 * (y_min + y_max), 0.5 * (z_min + z_max)),
                direction=(1, 0, 0),
                i_size=max(1.0, y_max - y_min),
                j_size=max(1.0, z_max - z_min),
                i_resolution=18,
                j_resolution=18,
            )
            self._seed_signature = seed_signature

        # 6. PORTINARI PRECISION INTEGRATION
        # Keep traces alive in slow zones; too-large cutoff causes "stuck at inlet".
        terminal_speed = max(local_max_speed * 1e-6, 1e-10)
        if self._seed_cache.n_points == 0:
            plotter.render()
            return

        # Wait until flow around obstacle is developed before freezing a
        # streamline solution, otherwise we freeze early straight lines.
        self._freeze_wait_frames += 1
        flow_developed = True
        if np.any(mask):
            obs_points = np.argwhere(mask)
            obs_x_min = int(np.min(obs_points[:, 0]))
            wake_x0 = min(Nx - 1, obs_x_min + 1)
            wake_x1 = min(Nx, obs_x_min + 10)
            y0 = max(0, int(np.floor(y_min)))
            y1 = min(Ny, int(np.ceil(y_max)) + 1)
            z0 = max(0, int(np.floor(z_min)))
            z1 = min(Nz, int(np.ceil(z_max)) + 1)

            wake_slice = np.s_[wake_x0:wake_x1, y0:y1, z0:z1]
            ux_wake = ux[wake_slice]
            uy_wake = uy[wake_slice]
            uz_wake = uz[wake_slice]
            transverse = np.mean(np.sqrt(uy_wake ** 2 + uz_wake ** 2))
            streamwise = np.mean(np.abs(ux_wake)) + 1e-12
            # Need at least some lateral deflection before freezing.
            flow_developed = (transverse / streamwise) > 0.03

        min_wait = 10
        if self._frozen_streamlines is None and (self._freeze_wait_frames < min_wait or not flow_developed):
            self.frame_count += 1
            plotter.render()
            return

        if self._frozen_streamlines is None:
            candidate = grid.streamlines_from_source(
                self._seed_cache,
                vectors="Velocity",
                integration_direction="forward",
                max_steps=5000,
                initial_step_length=0.12,
                terminal_speed=1e-12,
                integrator_type=2
            )

            if candidate.n_points > 0:
                x_coords = candidate.points[:, 0]
                y_coords = candidate.points[:, 1]
                x_span = float(np.max(x_coords) - np.min(x_coords))
                min_required_span = Nx * 0.45
                enough_points = candidate.n_points >= 400

                # Outlet-completion gate: require enough streamline points near the
                # downstream side and balanced top/bottom occupancy so we don't
                # freeze an almost-complete "pre-final" frame.
                outlet_x = Nx - 3
                outlet_band = np.abs(x_coords - outlet_x) <= 1.5
                outlet_points = int(np.count_nonzero(outlet_band))

                y_mid = 0.5 * (y_min + y_max)
                top_hits = int(np.count_nonzero(outlet_band & (y_coords >= y_mid)))
                bottom_hits = int(np.count_nonzero(outlet_band & (y_coords < y_mid)))
                balance_ratio = min(top_hits, bottom_hits) / (max(top_hits, bottom_hits) + 1e-12)

                # Expect a meaningful fraction of seed count to reach outlet band.
                expected_seed_count = max(1, int(self._seed_cache.n_points))
                outlet_completion = outlet_points / expected_seed_count
                outlet_ready = outlet_completion >= 0.40 and balance_ratio >= 0.55

                # Inlet-clean gate: near the seed side, flow should be mostly
                # streamwise (low transverse component), otherwise we are still in
                # an unstable transient ("weird at the start").
                inlet_x0 = max(0, inlet_x - 1)
                inlet_x1 = min(Nx, inlet_x + 5)
                inlet_slice = np.s_[inlet_x0:inlet_x1, :, :]
                inlet_fluid = ~mask[inlet_slice]
                if np.any(inlet_fluid):
                    ux_in = ux[inlet_slice][inlet_fluid]
                    uy_in = uy[inlet_slice][inlet_fluid]
                    uz_in = uz[inlet_slice][inlet_fluid]
                    inlet_stream = np.mean(np.abs(ux_in)) + 1e-12
                    inlet_trans = np.mean(np.sqrt(uy_in ** 2 + uz_in ** 2))
                    inlet_clean = (inlet_trans / inlet_stream) <= 0.10
                else:
                    inlet_clean = False

                valid_candidate = (
                    enough_points
                    and (x_span >= min_required_span)
                    and outlet_ready
                    and inlet_clean
                )
            else:
                valid_candidate = False

            # If the candidate is too local (spider/fan near obstacle), keep waiting
            # and retry on a later frame instead of freezing a bad result.
            if not valid_candidate:
                self.frame_count += 1
                plotter.render()
                return

            self._frozen_streamlines = candidate
            if (
                self._frozen_streamlines.n_points > 0
                and "IntegrationTime" in self._frozen_streamlines.point_data
            ):
                self._frozen_max_time = float(np.max(self._frozen_streamlines.point_data["IntegrationTime"]))
                self._streamlines_ready = True
            else:
                self._streamlines_ready = self._frozen_streamlines.n_points > 0

            # Hide streamlines until the full solution is ready.
            self.frame_count += 1
            plotter.render()
            return

        streamlines = self._frozen_streamlines
        if (
            self._streamlines_ready
            and self._reveal_time < self._frozen_max_time
            and streamlines is not None
            and streamlines.n_points > 0
            and self._frozen_max_time > 0.0
            and "IntegrationTime" in streamlines.point_data
        ):
            # Fake growth by revealing progressively from completed streamlines.
            self._reveal_time = min(self._frozen_max_time, self._reveal_time + 0.6)
            revealed = streamlines.threshold(
                value=(0.0, self._reveal_time),
                scalars="IntegrationTime"
            )
            if revealed.n_points > 0:
                streamlines = revealed
        elif (
            streamlines is not None
            and streamlines.n_points > 0
            and self._frozen_max_time > 0.0
            and "IntegrationTime" in streamlines.point_data
        ):
            revealed = streamlines.threshold(
                value=(0.0, self._frozen_max_time),
                scalars="IntegrationTime"
            )
            if revealed.n_points > 0:
                streamlines = revealed

        # 7. RENDER
        if streamlines is not None and streamlines.n_points > 0:
            # Decimate for readability: keep every 3rd streamline cell.
            if streamlines.n_cells > 3:
                keep_ids = np.arange(0, streamlines.n_cells, 3, dtype=np.int64)
                streamlines = streamlines.extract_cells(keep_ids)

            # Use Speed to color the lines (Standard CFD style)
            streamlines.point_data["Speed"] = np.linalg.norm(
                streamlines.point_data["Velocity"], axis=1
            )
            plotter.add_mesh(streamlines, scalars="Speed", cmap="turbo",
                             line_width=5, render_lines_as_tubes=True,
                             name="streamline_layer")

        self.frame_count += 1
        plotter.render()