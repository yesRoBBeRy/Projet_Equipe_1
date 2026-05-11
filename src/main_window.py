from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille
from src.Backend.Projection import Projection
from src.Backend.Parametres import Parametres
from src.Backend.Advections import Advections
from src.Backend.obstacle_from_scene import sync_obstacle_mask_from_scene
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QPushButton, QStackedWidget, QSizePolicy, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap

# PNG des obstacles : chemins relatifs au répertoire du projet (pas au CWD du processus).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Palette de couleurs de l'interface ──────────────────────────────────────
BG       = "#050d1a"   # Fond principal (bleu très sombre)
SURFACE  = "#091525"   # Surface des éléments
PANEL    = "#071020"   # Fond du panneau latéral
BORDER   = "#0e2a45"   # Bordure subtile
BORDER2  = "#1a4060"   # Bordure accentuée
CYAN     = "#00d4ff"   # Couleur d'accent principale
CYAN_DIM = "#007a99"   # Cyan atténué (titres de section)
ORANGE   = "#ff6b1a"   # Couleur du bouton reset
GREEN    = "#00ff88"   # Couleur du bouton lancer
RED      = "#ff3333"   # Couleur d'alerte / arrêt
TEXT     = "#c8e8ff"   # Texte principal
TEXT2    = "#4a7a9b"   # Texte secondaire (labels)
TEXT3    = "#1a3a55"   # Texte tertiaire (peu utilisé)
MONO     = '"Consolas","Courier New",monospace'  # Police monospace

# ── Feuille de style globale de l'application ────────────────────────────────
APP_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: {MONO};
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    background: {BG};
    border: 2px solid {CYAN};
    margin: -6px 0;
}}
QSlider::handle:horizontal:hover {{
    background: {CYAN};
    border-color: #ffffff;
}}
QSlider::sub-page:horizontal {{
    background: {CYAN};
    border-radius: 3px;
    height: 6px;
}}
QSlider::add-page:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}
QPushButton {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER2};
    border-radius: 6px;
    padding: 10px 16px;
    font-family: {MONO};
    font-size: 13px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background: #0d2035;
    border: 1px solid {CYAN};
    color: {CYAN};
}}
QPushButton:pressed {{
    background: rgba(0,212,255,0.15);
    border-color: {CYAN};
    color: {CYAN};
}}
"""


class HLine(QFrame):
    """Séparateur horizontal fin utilisé entre les sections du panneau."""
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER}; border: none;")


class SectionTitle(QLabel):
    """Label stylisé servant de titre de section (ex: 'OBSTACLES', 'PARAMÈTRES FLUIDE')."""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {CYAN_DIM};
            font-size: 10px;
            font-family: {MONO};
            letter-spacing: 3px;
            padding: 8px 0 4px 0;
        """)


class MainWindow(QMainWindow):
    """
    Fenêtre principale de la simulation de dynamique des fluides.

    Contient :
    - Un viewport 3D (Scene3D / PyVista) à gauche
    - Un panneau de contrôle à droite géré par un QStackedWidget :
        * Page 0 : contrôles généraux (run/reset, choix d'obstacle, paramètres fluide)
        * Page 1 : configuration d'une forme sélectionnée (dimensions + position XYZ)
    """

    def __init__(self):
        super().__init__()

        # ── État interne ──────────────────────────────────────────────────────
        self.pause = True                   # True = simulation arrêtée
        self._shape_config_open = False      # True = page forme ouverte → pas de streamlines
        self.forme_selectionnee = None      # Nom de la forme en cours de configuration
        self.grille = Grille(50, 50, 50)    # Aligné sur dev_elliot pour le backend
        self.police_scientifique = QFont("Consolas", 13)

        # ── Fenêtre ───────────────────────────────────────────────────────────
        self.resize(1280, 720)
        self.setWindowTitle("DYNAMIQUE DES FLUIDES SIM")
        self.setStyleSheet(APP_STYLE)

        # ── Widget central et layout principal (horizontal) ───────────────────
        self.centre = QWidget()
        self.setCentralWidget(self.centre)
        self.layout_principal = QHBoxLayout(self.centre)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # ── Zone viewport 3D (côté gauche) ───────────────────────────────────
        self.scene_containerScene = QWidget()
        self.scene_containerScene.setStyleSheet(f"background:{BG};")
        self.scene_layoutScene3D = QVBoxLayout(self.scene_containerScene)
        self.scene_layoutScene3D.setContentsMargins(0, 0, 0, 0)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.layout_principal.addWidget(self.scene_containerScene)

        self.parametres = Parametres(0.0, 0.0, 0.0, 101.4, 20.0, grille=self.grille)
        self.advection = Advections(self.parametres)
        self.visualisation = Projection(self.parametres, self.scene.grille_3D)

        self.scene.forme.connect(self.recevoir_forme)

        # --- Stack pour panneau / édition ---
        # ── Pile de panneaux latéraux (côté droit) ───────────────────────────
        self.stack = QStackedWidget()
        self.forme_en_scene = None  # Référence à l'acteur temporaire affiché

        # ════════════════════════════════════════════════════════════════════
        # PAGE 0 — Panneau de contrôle principal
        # ════════════════════════════════════════════════════════════════════
        self.panneau = QWidget()
        self.panneau.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        self.layout_controles = QVBoxLayout(self.panneau)
        self.layout_controles.setContentsMargins(18, 16, 18, 16)
        self.layout_controles.setSpacing(25)

        # ── En-tête : titre + indicateur de statut ────────────────────────
        ligne_principale = QHBoxLayout()
        title_lbl = QLabel("FLUID SIM")
        title_lbl.setStyleSheet(f"""
            color: {CYAN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        self.status_dot = QLabel("◉ RUN")
        self.status_dot.setStyleSheet(f"""
            color: {TEXT2};
            font-size: 11px;
            letter-spacing: 2px;
        """)
        ligne_principale.addWidget(title_lbl)
        ligne_principale.addStretch()
        ligne_principale.addWidget(self.status_dot)
        self.layout_controles.addLayout(ligne_principale)
        self.layout_controles.addWidget(HLine())
        self.layout_controles.addSpacing(4)

        # ── Boutons RUN / RESET ───────────────────────────────────────────
        self.boutons = QHBoxLayout()
        self.boutons.setSpacing(8)

        self.boutonRun = QPushButton("▶  LANCER")
        self.boutonRun.setFixedHeight(46)
        self.boutonRun.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,255,136,0.08);
                color: {GREEN};
                border: 1px solid rgba(0,255,136,0.5);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
        """)

        self.bouton_reset = QPushButton("↺")
        self.bouton_reset.setFixedSize(46, 46)
        self.bouton_reset.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,26,0.08);
                color: {ORANGE};
                border: 1px solid rgba(255,107,26,0.4);
                border-radius: 6px;
                font-size: 18px;
            }}
            QPushButton:hover {{ background: rgba(255,107,26,0.18); border-color: {ORANGE}; }}
        """)

        self.boutons.addWidget(self.boutonRun)
        self.boutons.addWidget(self.bouton_reset)
        self.boutonRun.clicked.connect(self.animerRun)
        self.bouton_reset.clicked.connect(self.animerReset)
        self.layout_controles.addLayout(self.boutons)
        self.layout_controles.addSpacing(8)
        self.layout_controles.addWidget(HLine())

        # ── Grille de sélection des obstacles géométriques ────────────────
        self.layout_controles.addWidget(SectionTitle("OBSTACLES"))

        self.formesGeometriqueLigneDuHaut = QHBoxLayout()
        self.formesGeometriqueLigneDuHaut.setSpacing(6)
        self.formesGeometriqueLigneDuBas  = QHBoxLayout()
        self.formesGeometriqueLigneDuBas.setSpacing(6)

        # (image, identifiant_forme, couleur_unused, ligne_cible)
        formes_config = [
            ("realSphere.png", "sphere",   "red", self.formesGeometriqueLigneDuHaut),
            ("prisme.png",     "prisme",   "red", self.formesGeometriqueLigneDuHaut),
            ("cube.png",       "cube",     "red", self.formesGeometriqueLigneDuHaut),
            ("cylindre.png",   "cylindre", "red", self.formesGeometriqueLigneDuBas),
            ("Pyramide.png",   "pyramide", "red", self.formesGeometriqueLigneDuBas),
            ("fleche.png",     "fleche",   "red", self.formesGeometriqueLigneDuBas),
        ]

        # Création dynamique d'un bouton icône pour chaque forme
        for image, forme, couleur, ligne in formes_config:
            btn = QPushButton("")
            btn.setIcon(QPixmap(str(_PROJECT_ROOT / image)))
            btn.setIconSize(QSize(60, 60))
            btn.setFixedSize(90, 90)
            btn.setToolTip(forme.upper())
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {SURFACE};
                    border: 1px solid {BORDER2};
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background: rgba(0,212,255,0.12);
                    border: 1px solid {CYAN};
                }}
                QPushButton:pressed {{
                    background: rgba(0,212,255,0.25);
                    border: 2px solid {CYAN};
                }}
            """)
            # Capture de `forme` par défaut pour éviter la closure tardive
            btn.clicked.connect(lambda checked, f=forme: self.ouvrir_panneau_forme(f))
            ligne.addWidget(btn)

        self.layout_controles.addLayout(self.formesGeometriqueLigneDuHaut)
        self.layout_controles.addSpacing(6)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuBas)
        self.layout_controles.addSpacing(4)
        self.layout_controles.addWidget(HLine())

        # ── Sliders des paramètres physiques du fluide ────────────────────
        self.layout_controles.addWidget(SectionTitle("PARAMÈTRES FLUIDE"))

        self.texte_temperature, self.slider_temperature = self.creer_bloc("Température", 0, 30,    "°C")
        self.layout_controles.addSpacing(6)
        self.texte_viscous,     self.slider_viscous     = self.creer_bloc("Viscosité",   0, 1000,  "mPa")
        self.layout_controles.addSpacing(6)
        # facteur=10 pour obtenir une résolution décimale (ex: 101.4 kPa)
        self.texte_pression,    self.slider_pression    = self.creer_bloc("Pression",    0, 301.4, "kPa", 10)
        self.layout_controles.addSpacing(6)
        self.texte_vitesse,     self.slider_vitesse     = self.creer_bloc("Vitesse",     0, 100,   "m/s")
        self.layout_controles.addSpacing(10)
        self.bouton_confirmer_fluide = QPushButton("✔  APPLIQUER LES PARAMÈTRES")
        self.bouton_confirmer_fluide.setFixedHeight(42)
        self.bouton_confirmer_fluide.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,212,255,0.10);
                color: {CYAN};
                border: 1px solid rgba(0,212,255,0.5);
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover:enabled {{ background: rgba(0,212,255,0.22); }}
            QPushButton:disabled {{
                background: rgba(40,55,70,0.35);
                color: {TEXT2};
                border: 1px solid {BORDER2};
            }}
        """)
        self.bouton_confirmer_fluide.setToolTip(
            "Applique les curseurs au fluide (LBM) sans effacer la scène, puis relance la simulation."
        )
        self.bouton_confirmer_fluide.clicked.connect(self.confirmer_parametres_fluide)
        self.layout_controles.addWidget(self.bouton_confirmer_fluide)
        self._fluide_dernier_applique = self._fluide_lire_etat_curseurs()
        for _s in (
            self.slider_temperature,
            self.slider_viscous,
            self.slider_pression,
            self.slider_vitesse,
        ):
            _s.valueChanged.connect(self._on_fluide_slider_changed)
        self._maj_bouton_appliquer_fluide()
        self.layout_controles.addStretch()

        # ════════════════════════════════════════════════════════════════════
        # PAGE 1 — Panneau de configuration d'une forme
        # ════════════════════════════════════════════════════════════════════
        self.scene2_container = QWidget()
        self.scene2_container.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        _outer_scene2 = QVBoxLayout(self.scene2_container)
        _outer_scene2.setContentsMargins(0, 0, 0, 0)
        _outer_scene2.setSpacing(0)
        self.scene2_scroll = QScrollArea(self.scene2_container)
        self.scene2_scroll.setWidgetResizable(True)
        self.scene2_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scene2_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scene2_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scene2_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        _outer_scene2.addWidget(self.scene2_scroll)

        self.scene2_inner = QWidget()
        self.scene2_inner.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.scene2_layout = QVBoxLayout(self.scene2_inner)
        self.scene2_layout.setContentsMargins(18, 16, 18, 16)
        self.scene2_layout.setSpacing(14)
        self.scene2_scroll.setWidget(self.scene2_inner)

        # ── Bouton retour vers la page principale ─────────────────────────
        btn_back = QPushButton("← RETOUR")
        btn_back.setFixedHeight(38)
        btn_back.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(btn_back)
        self.scene2_layout.addWidget(HLine())

        # ── Nom de la forme sélectionnée ──────────────────────────────────
        self.label_forme_choisie = QLabel("FORME")
        self.label_forme_choisie.setFont(self.police_scientifique)
        self.label_forme_choisie.setStyleSheet(f"""
            color: {CYAN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 3px;
            padding: 6px 0 2px 0;
        """)
        self.scene2_layout.addWidget(self.label_forme_choisie)

        # ── Zone de sliders spécifiques à la forme (générée dynamiquement) ─
        self.layout_sliders_forme = QVBoxLayout()
        self.layout_sliders_forme.setSpacing(8)
        self.scene2_layout.addLayout(self.layout_sliders_forme)
        self.sliders_forme = {}
        self.labels_forme = {}

        # ── Sliders de position XYZ ───────────────────────────────────────
        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addWidget(SectionTitle("POSITION"))

        self.sliders_xyz = {}  # { 'x'|'y'|'z': QSlider }
        self.labels_xyz = {}  # { 'x'|'y'|'z': QLabel }
        for axe, max_val in zip(["X", "Y", "Z"], [self.grille.x, self.grille.y, self.grille.z]):
            ligne = QHBoxLayout()
            ligne.setSpacing(10)

            axe_lbl = QLabel(axe)
            axe_lbl.setFixedWidth(16)
            axe_lbl.setStyleSheet(f"color:{CYAN}; font-size:25px; font-weight:bold;")

            # Centièmes : plage symétrique pour positions négatives ou positives
            lim = int(max_val * 100)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(-lim, lim)
            slider.setValue(0)

            label_axe = QLabel("0.00")
            label_axe.setFixedWidth(54)
            label_axe.setFont(self.police_scientifique)
            label_axe.setStyleSheet(f"color:{TEXT}; font-size:13px;")

            ax_key = axe.lower()
            slider.valueChanged.connect(
                lambda v, lbl=label_axe, ak=ax_key: self._on_xyz_slider_moved(v, lbl, ak)
            )

            ligne.addWidget(axe_lbl)
            ligne.addWidget(slider)
            ligne.addWidget(label_axe)
            self.scene2_layout.addLayout(ligne)
            self.sliders_xyz[ax_key] = slider
            self.labels_xyz[ax_key] = label_axe

        # ── Sliders de rotation Rx Ry Rz (degrés, centièmes) ───────────────
        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addWidget(SectionTitle("ROTATION (°)"))
        self.sliders_rot = {}
        self.labels_rot = {}
        for nom_axe, cle in [("Rx", "rx"), ("Ry", "ry"), ("Rz", "rz")]:
            ligne_r = QHBoxLayout()
            ligne_r.setSpacing(10)
            axe_lbl = QLabel(nom_axe)
            axe_lbl.setFixedWidth(28)
            axe_lbl.setStyleSheet(f"color:{CYAN}; font-size:22px; font-weight:bold;")
            slider_r = QSlider(Qt.Horizontal)
            slider_r.setRange(-18000, 18000)
            slider_r.setValue(0)
            label_r = QLabel("0.00")
            label_r.setFixedWidth(54)
            label_r.setFont(self.police_scientifique)
            label_r.setStyleSheet(f"color:{TEXT}; font-size:13px;")
            slider_r.valueChanged.connect(lambda _v: self._apply_rotation_combined())
            ligne_r.addWidget(axe_lbl)
            ligne_r.addWidget(slider_r)
            ligne_r.addWidget(label_r)
            self.scene2_layout.addLayout(ligne_r)
            self.sliders_rot[cle] = slider_r
            self.labels_rot[cle] = label_r

        # ── Affinage rotation : même unité (centi°) mais plage courte ±5° ─
        self.scene2_layout.addWidget(SectionTitle("AFFINAGE ROT. (±5°)"))
        self.sliders_rot_fine = {}
        self.labels_rot_fine = {}
        for nom_axe, cle in [("Δx", "rx"), ("Δy", "ry"), ("Δz", "rz")]:
            ligne_f = QHBoxLayout()
            ligne_f.setSpacing(10)
            axe_f = QLabel(nom_axe)
            axe_f.setFixedWidth(28)
            axe_f.setStyleSheet(f"color:{TEXT2}; font-size:18px; font-weight:bold;")
            slider_f = QSlider(Qt.Horizontal)
            slider_f.setRange(-500, 500)
            slider_f.setValue(0)
            label_f = QLabel("+0.00")
            label_f.setFixedWidth(54)
            label_f.setFont(self.police_scientifique)
            label_f.setStyleSheet(f"color:{TEXT}; font-size:13px;")
            slider_f.valueChanged.connect(lambda _v: self._apply_rotation_combined())
            ligne_f.addWidget(axe_f)
            ligne_f.addWidget(slider_f)
            ligne_f.addWidget(label_f)
            self.scene2_layout.addLayout(ligne_f)
            self.sliders_rot_fine[cle] = slider_f
            self.labels_rot_fine[cle] = label_f

        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addSpacing(6)

        # ── Bouton CONFIRMER ──────────────────────────────────────────────
        self.bouton_confirmer = QPushButton("✔  CONFIRMER")
        self.bouton_confirmer.setFixedHeight(44)
        self.bouton_confirmer.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,212,255,0.10);
                color: {CYAN};
                border: 1px solid rgba(0,212,255,0.5);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,212,255,0.22); }}
        """)
        self.bouton_confirmer.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(self.bouton_confirmer)

        # ── Bouton SUPPRIMER ──────────────────────────────────────────────
        self.bouton_supprimer = QPushButton("✕  SUPPRIMER")
        self.bouton_supprimer.setFixedHeight(44)
        self.bouton_supprimer.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,51,51,0.08);
                color: {RED};
                border: 1px solid rgba(255,51,51,0.4);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(255,51,51,0.20); }}
        """)
        self.bouton_supprimer.clicked.connect(self.supprimer_forme)
        self.scene2_layout.addWidget(self.bouton_supprimer)

        # ── Ajout des deux pages dans la pile et insertion dans le layout ─
        self.stack.addWidget(self.panneau)          # index 0
        self.stack.addWidget(self.scene2_container) # index 1
        self.layout_principal.addWidget(self.stack)

        # ── Définition des paramètres ajustables par forme ────────────────
        # Format : { nom_forme: [(nom_param, min, max), ...] }
        # Plages max augmentées (repère grille ~50³ ; ajuster si la grille change)
        _mx = 22
        self.parametres_formes = {
            "sphere":   [("rayon", 1, _mx)],
            "cube":     [("c", 1, _mx)],
            "cylindre": [("rayon", 1, _mx), ("h", 1, _mx)],
            "prisme":   [("l", 1, _mx), ("w", 1, _mx), ("h", 1, _mx)],
            "pyramide": [("h", 1, _mx)],
            "fleche":   [("l", 1, _mx), ("w", 1, _mx)],
        }

        # ── Timer de la boucle de simulation (cible ~30 fps) ─────────────
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

        # Sync obstacle précis après la fin des mouvements de sliders (évite le gros coût VTK à chaque tick).
        self._obstacle_full_sync_timer = QTimer(self)
        self._obstacle_full_sync_timer.setSingleShot(True)
        self._obstacle_full_sync_timer.setInterval(220)
        self._obstacle_full_sync_timer.timeout.connect(self._sync_obstacle_full_after_shape_idle)

    def _sync_obstacle_while_editing_shape(self):
        sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=True)
        self._obstacle_full_sync_timer.start(220)

    def _sync_obstacle_full_after_shape_idle(self):
        if self._shape_config_open and self.forme_en_scene is not None:
            sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=False)

    def _flush_scene_render(self):
        if hasattr(self.scene, "_render_coalesce_timer"):
            self.scene._render_coalesce_timer.stop()
        if hasattr(self.scene, "_flush_plotter_render"):
            self.scene._flush_plotter_render()

    def _on_xyz_slider_moved(self, v, label_axe, axis: str):
        """Met à jour le label et déplace la forme en direct dans la vue 3D."""
        label_axe.setText(f"{v / 100:.2f}")
        if self.forme_en_scene is None:
            return
        if self.forme_en_scene not in self.scene.pos_current:
            return
        pos = v / 100.0
        x, y, z = self.scene.pos_current[self.forme_en_scene]
        self.scene.acteur_current = self.forme_en_scene
        if axis == "x":
            self.scene.deplacement(pos, y, z)
        elif axis == "y":
            self.scene.deplacement(x, pos, z)
        else:
            self.scene.deplacement(x, y, pos)
        self._sync_obstacle_while_editing_shape()

    def _apply_rotation_combined(self):
        """Rotation totale = grossier (±180°) + affinage (±5°), labels et scène."""
        if self.forme_en_scene is None:
            return
        if self.forme_en_scene not in self.scene.pos_current:
            return
        for k in ("rx", "ry", "rz"):
            c = self.sliders_rot[k].value()
            f = self.sliders_rot_fine[k].value()
            total_c = c + f
            self.labels_rot[k].setText(f"{total_c / 100:.2f}")
            self.labels_rot_fine[k].setText(f"{f / 100:+.2f}")
        rx = (self.sliders_rot["rx"].value() + self.sliders_rot_fine["rx"].value()) / 100.0
        ry = (self.sliders_rot["ry"].value() + self.sliders_rot_fine["ry"].value()) / 100.0
        rz = (self.sliders_rot["rz"].value() + self.sliders_rot_fine["rz"].value()) / 100.0
        self.scene.acteur_current = self.forme_en_scene
        self.scene.set_rotation(rx, ry, rz)
        self._sync_obstacle_while_editing_shape()

    def generer_sliders_forme(self, nom_forme):
        self.sliders_forme.clear()
        # Suppression des anciens widgets du layout
        while self.layout_sliders_forme.count():
            item = self.layout_sliders_forme.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.sliders_forme.clear()
        self.labels_forme.clear()

        for param, min_val, max_val in self.parametres_formes.get(nom_forme, []):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setSpacing(10)

            param_lbl = QLabel(param.upper())
            param_lbl.setFixedWidth(52)
            param_lbl.setStyleSheet(f"color:{TEXT2}; font-size:12px; letter-spacing:1px;")

            # Valeur en centièmes pour la précision décimale
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(min_val * 100))

            label = QLabel(f"{min_val:.2f}")
            label.setFixedWidth(42)
            label.setFont(self.police_scientifique)
            label.setStyleSheet(f"color:{TEXT}; font-size:13px;")

            slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v / 100:.2f}"))

            layout.addWidget(param_lbl)
            layout.addWidget(slider)
            layout.addWidget(label)

            self.layout_sliders_forme.addWidget(container)
            self.sliders_forme[param] = slider
            self.labels_forme[param] = label

    def creer_bloc(self, nom, min_val, max_val, unite="", facteur=1):
        """
        Crée un bloc label + slider pour un paramètre physique du fluide,
        l'ajoute au panneau principal et retourne (QLabel_nom, QSlider).

        Args:
            nom      : Nom du paramètre (affiché en majuscules).
            min_val  : Valeur minimale réelle du paramètre.
            max_val  : Valeur maximale réelle du paramètre.
            unite    : Unité affichée à côté de la valeur (ex: '°C').
            facteur  : Multiplicateur interne du slider (utile pour les décimales).
        """
        bloc = QVBoxLayout()
        bloc.setSpacing(6)

        ligne = QHBoxLayout()
        texte = QLabel(nom.upper())
        texte.setStyleSheet(f"color:{TEXT2}; font-size:12px; letter-spacing:1px;")
        label_valeur = QLabel(f"{min_val} {unite}")
        label_valeur.setFont(self.police_scientifique)
        label_valeur.setStyleSheet(f"color:{CYAN}; font-size:14px; font-weight:bold;")
        ligne.addWidget(texte)
        ligne.addStretch()
        ligne.addWidget(label_valeur)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * facteur), int(max_val * facteur))
        slider.valueChanged.connect(
            lambda v, l=label_valeur, u=unite, f=facteur: self.update_value(l, v, u, f)
        )
        bloc.addLayout(ligne)
        bloc.addWidget(slider)
        self.layout_controles.addLayout(bloc)
        return texte, slider

    def _connecter_sliders_forme(self):
        for param, slider in self.sliders_forme.items():
            try:
                slider.valueChanged.disconnect()
            except TypeError:
                pass
            label = self.labels_forme[param]
            slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v / 100:.2f}"))
            slider.valueChanged.connect(self.mettre_a_jour_dimensions)



    def ouvrir_panneau_forme(self, nom_forme):
        """
        Bascule vers la page 1 (configuration de forme) :
        - Met à jour le titre et réinitialise les sliders XYZ.
        - Génère les sliders propres à la forme sélectionnée.
        - Crée une forme temporaire dans la scène 3D.
        - Connecte chaque slider de dimension à mettre_a_jour_dimensions.
        """
        self._shape_config_open = True
        self._obstacle_full_sync_timer.stop()
        self.visualisation.clear_streamlines()
        self.forme_selectionnee = nom_forme
        self.label_forme_choisie.setText(nom_forme.upper())

        # Réinitialisation de la position à l'origine (sans déclencher les slots XYZ)
        for slider in self.sliders_xyz.values():
            slider.blockSignals(True)
            slider.setValue(0)
        for slider in self.sliders_xyz.values():
            slider.blockSignals(False)
        for k in self.labels_xyz:
            self.labels_xyz[k].setText("0.00")
        for slider in self.sliders_rot.values():
            slider.blockSignals(True)
            slider.setValue(0)
        for slider in self.sliders_rot.values():
            slider.blockSignals(False)
        for k in self.labels_rot:
            self.labels_rot[k].setText("0.00")
        for slider in self.sliders_rot_fine.values():
            slider.blockSignals(True)
            slider.setValue(0)
        for slider in self.sliders_rot_fine.values():
            slider.blockSignals(False)
        for k in self.labels_rot_fine:
            self.labels_rot_fine[k].setText("+0.00")

        self.generer_sliders_forme(nom_forme)

        # Valeurs par défaut = minima de chaque paramètre
        default_valeurs = {param: min_val for param, min_val, max_val in self.parametres_formes.get(nom_forme, [])}
        self.forme_en_scene = self.scene.add_forme(nom_forme, default_valeurs)
        self.scene.acteur_current = self.forme_en_scene


        self._connecter_sliders_forme()

        self.stack.setCurrentIndex(1)
        sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=False)
        self.scene.set_editing_highlight(self.forme_en_scene)
        self._flush_scene_render()

    def confirmer_forme(self):
        """Revient à la page principale (index 0) sans supprimer la forme."""
        self._obstacle_full_sync_timer.stop()
        self._flush_scene_render()
        self.scene.set_editing_highlight(None)
        self._shape_config_open = False
        self.stack.setCurrentIndex(0)
        sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=False)
        self.visualisation.afficher_streamlines()

    def supprimer_forme(self):
        """
        Supprime l'acteur 3D temporaire de la scène et revient au panneau principal.
        """
        if self.forme_en_scene is not None:
            self.scene.set_editing_highlight(None)
            self.scene.supprimer(self.scene.acteur_current)
        self.forme_en_scene = None
        self._obstacle_full_sync_timer.stop()
        self._shape_config_open = False
        self.stack.setCurrentIndex(0)
        sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=False)
        self.visualisation.clear_streamlines()
        self.visualisation.afficher_streamlines()

    def mettre_a_jour_dimensions(self):
        """
        Appelée à chaque changement d'un slider de dimension de forme.
        Lit toutes les valeurs courantes et les transmet à la scène 3D.
        """
        if self.forme_en_scene is None:
            return
        valeurs = {nom: slider.value() / 100 for nom, slider in self.sliders_forme.items()}
        self.scene.acteur_current = self.forme_en_scene
        self.scene.changer_dimensions_dict(valeurs)
        self._sync_obstacle_while_editing_shape()

    def update_value(self, label, value, unite, facteur):
        """
        Met à jour le label d'affichage d'un paramètre fluide.
        Affiche un flottant si facteur > 1, sinon un entier.
        """
        valeur_reelle = value / facteur
        if facteur > 1:
            label.setText(f"{valeur_reelle:.2f} {unite}")
        else:
            label.setText(f"{int(valeur_reelle)} {unite}")

    def update_simulation(self):
        """
        Slot appelé à chaque tick du timer (~30 fps).
        Avance la simulation d'un pas et rafraîchit la scène 3D.
        """
        if self.scene._obstacle_revision != self.scene._obstacle_mask_synced_rev:
            sync_obstacle_mask_from_scene(self.scene, self.parametres)
        self.advection.mise_a_jour()
        self.scene.grille_3D.update_scene()
        if not self._shape_config_open:
            self.visualisation.record_lbm_step_for_streamlines()
            self.visualisation.afficher_streamlines()

    def animerRun(self):
        """
        Bascule entre l'état RUNNING et IDLE :
        - IDLE → RUNNING : démarre le timer, met à jour le bouton en rouge.
        - RUNNING → IDLE : arrête le timer, remet le bouton en vert.
        """
        if not self.pause:
            # ── Passage à IDLE ────────────────────────────────────────────
            self.boutonRun.setText("▶  LANCER")
            self.boutonRun.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,255,136,0.08);
                    color: {GREEN};
                    border: 1px solid rgba(0,255,136,0.5);
                    border-radius: 6px;
                    font-size: 14px; font-weight: bold; letter-spacing: 2px;
                }}
                QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
            """)
            self.status_dot.setText("◉ IDLE")
            self.status_dot.setStyleSheet(f"color:{TEXT2}; font-size:11px; letter-spacing:2px;")
            self.timer.stop()
            self.visualisation.remove_streamline_layer()
        else:
            # ── Passage à RUNNING ─────────────────────────────────────────
            self.boutonRun.setText("■  ARRÊTER")
            self.boutonRun.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,51,51,0.10);
                    color: {RED};
                    border: 1px solid rgba(255,51,51,0.5);
                    border-radius: 6px;
                    font-size: 14px; font-weight: bold; letter-spacing: 2px;
                }}
                QPushButton:hover {{ background: rgba(255,51,51,0.22); border-color: {RED}; }}
            """)
            self.status_dot.setText("◉ RUN")
            self.status_dot.setStyleSheet(f"color:{GREEN}; font-size:11px; letter-spacing:2px;")
            self.visualisation.reset_streamline_warmup()
            self.timer.start(1000 // 30)  # ~30 fps
        self.pause = not self.pause

    def animerReset(self):
        """
        Réinitialise complètement la simulation :
        - Arrête le timer et passe en état IDLE.
        - Détruit et recrée la scène 3D et la grille.
        - Remet tous les sliders de paramètres fluide à zéro.
        """
        self.timer.stop()
        self.pause = True
        self.boutonRun.setText("▶  LANCER")
        self.boutonRun.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,255,136,0.08);
                color: {GREEN};
                border: 1px solid rgba(0,255,136,0.5);
                border-radius: 6px;
                font-size: 14px; font-weight: bold; letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
        """)
        self.status_dot.setText("◉ IDLE")
        self.status_dot.setStyleSheet(f"color:{TEXT2}; font-size:11px; letter-spacing:2px;")

        # ── Remplacement de la scène PyVista ──────────────────────────────
        self.scene.plotter.close()
        self.scene_layoutScene3D.removeWidget(self.scene.plotter)
        self.scene.plotter.deleteLater()

        self.grille = Grille(50, 50, 50)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.scene.forme.connect(self.recevoir_forme)

        self.parametres = Parametres(0.0, 0.0, 0.0, 101.4, 20.0, grille=self.grille)
        self.advection = Advections(self.parametres)
        self.visualisation = Projection(self.parametres, self.scene.grille_3D)

        # ── Remise à zéro des paramètres fluide ───────────────────────────
        self.slider_temperature.setValue(0)
        self.slider_viscous.setValue(0)
        self.slider_pression.setValue(0)
        self.slider_vitesse.setValue(0)

        self._shape_config_open = False
        self.forme_en_scene = None
        self.stack.setCurrentIndex(0)
        self.visualisation.clear_streamlines()
        self._fluide_dernier_applique = self._fluide_lire_etat_curseurs()
        self._maj_bouton_appliquer_fluide()

    def _fluide_lire_etat_curseurs(self):
        """État brut des 4 curseurs fluide (entiers slider, pression ×10 incluse)."""
        return (
            self.slider_temperature.value(),
            self.slider_viscous.value(),
            self.slider_pression.value(),
            self.slider_vitesse.value(),
        )

    def _maj_bouton_appliquer_fluide(self):
        """Active le bouton seulement si un curseur diffère du dernier lot appliqué."""
        cur = self._fluide_lire_etat_curseurs()
        self.bouton_confirmer_fluide.setEnabled(cur != self._fluide_dernier_applique)

    def _on_fluide_slider_changed(self, _value=None):
        self._maj_bouton_appliquer_fluide()

    def confirmer_parametres_fluide(self):
        """
        Applique les valeurs des curseurs « Paramètres fluide » et repart d’un
        état LBM cohérent (F, τ, ρ…), sans recréer la scène 3D ni les obstacles.
        Arrête brièvement la boucle si elle tournait, puis relance la simulation.
        """
        if not self.pause:
            self.timer.stop()
            self.pause = True
            self.boutonRun.setText("▶  LANCER")
            self.boutonRun.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,255,136,0.08);
                    color: {GREEN};
                    border: 1px solid rgba(0,255,136,0.5);
                    border-radius: 6px;
                    font-size: 14px; font-weight: bold; letter-spacing: 2px;
                }}
                QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
            """)
            self.status_dot.setText("◉ IDLE")
            self.status_dot.setStyleSheet(f"color:{TEXT2}; font-size:11px; letter-spacing:2px;")
            self.visualisation.remove_streamline_layer()

        T = float(self.slider_temperature.value())
        mu = float(self.slider_viscous.value())
        P = float(self.slider_pression.value()) / 10.0
        V = float(self.slider_vitesse.value())
        self.parametres.appliquer_parametres_fluide(T, mu, P, V)
        self.parametres.grille.valeurs["densite"] = self.parametres.rho.copy()
        self.visualisation.clear_streamlines()
        self.scene.grille_3D.update_scene()
        self._fluide_dernier_applique = self._fluide_lire_etat_curseurs()
        self._maj_bouton_appliquer_fluide()

        if self.pause:
            self.animerRun()

    def recevoir_forme(self, acteur):
        if acteur is None:
            return

        self._obstacle_full_sync_timer.stop()
        self.forme_en_scene = acteur
        self.scene.acteur_current = acteur

        params = self.scene.parametres_formes.get(acteur)
        if params is None:
            return

        nom_forme = params["type"]
        self.label_forme_choisie.setText(nom_forme.capitalize())

        self.generer_sliders_forme(nom_forme)
        self._connecter_sliders_forme()

        for nom, slider in self.sliders_forme.items():
            valeur = params["params"].get(nom, 1)
            slider.blockSignals(True)
            slider.setValue(int(valeur * 100))
            slider.blockSignals(False)
            self.labels_forme[nom].setText(f"{valeur:.2f}")

        if acteur in self.scene.pos_current:
            x, y, z = self.scene.pos_current[acteur]
            for s in self.sliders_xyz.values():
                s.blockSignals(True)
            self.sliders_xyz["x"].setValue(int(x * 100))
            self.sliders_xyz["y"].setValue(int(y * 100))
            self.sliders_xyz["z"].setValue(int(z * 100))
            for s in self.sliders_xyz.values():
                s.blockSignals(False)
            self.labels_xyz["x"].setText(f"{x:.2f}")
            self.labels_xyz["y"].setText(f"{y:.2f}")
            self.labels_xyz["z"].setText(f"{z:.2f}")

        if acteur in self.scene.rot_current:
            rx, ry, rz = self.scene.rot_current[acteur]

            def split_axis(t_deg: float) -> tuple[int, int]:
                """Répartit l’angle en grossier (±180°) + affinage (±5°) en centi-degrés."""
                tc = int(round(t_deg * 100))
                tc = max(-18500, min(18500, tc))
                coarse = max(-18000, min(18000, tc))
                fine = tc - coarse
                return coarse, fine

            pairs = {
                "rx": split_axis(rx),
                "ry": split_axis(ry),
                "rz": split_axis(rz),
            }
            for s in list(self.sliders_rot.values()) + list(self.sliders_rot_fine.values()):
                s.blockSignals(True)
            for k in ("rx", "ry", "rz"):
                c, f = pairs[k]
                self.sliders_rot[k].setValue(c)
                self.sliders_rot_fine[k].setValue(f)
            for s in list(self.sliders_rot.values()) + list(self.sliders_rot_fine.values()):
                s.blockSignals(False)
            self._apply_rotation_combined()

        self._shape_config_open = True
        self.visualisation.clear_streamlines()
        self.stack.setCurrentIndex(1)
        self._obstacle_full_sync_timer.stop()
        sync_obstacle_mask_from_scene(self.scene, self.parametres, fast=False)
        self.scene.set_editing_highlight(acteur)
        self._flush_scene_render()