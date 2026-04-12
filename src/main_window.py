from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QStackedWidget
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap


# ╔══════════════════════════════════════════════════════════════╗
# ║  Remplace UNIQUEMENT ta classe MainWindow par ce fichier.   ║
# ║  Garde tout le reste de ton code intact.                    ║
# ╚══════════════════════════════════════════════════════════════╝

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QPushButton, QStackedWidget, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap

# ──────────────────────────────────────────────────────────────
# PALETTE AÉROSPATIALE
# ──────────────────────────────────────────────────────────────
BG       = "#050d1a"
SURFACE  = "#091525"
PANEL    = "#071020"
BORDER   = "#0e2a45"
BORDER2  = "#1a4060"
CYAN     = "#00d4ff"
CYAN_DIM = "#007a99"
ORANGE   = "#ff6b1a"
GREEN    = "#00ff88"
RED      = "#ff3333"
TEXT     = "#c8e8ff"
TEXT2    = "#4a7a9b"
TEXT3    = "#1a3a55"
MONO     = '"Consolas","Courier New",monospace'

# ──────────────────────────────────────────────────────────────
# STYLESHEET GLOBALE
# ──────────────────────────────────────────────────────────────
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
    width: 20px;
    height: 20px;
    border-radius: 10px;
    background: {BG};
    border: 2px solid {CYAN};
    margin: -8px 0;
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

# ──────────────────────────────────────────────────────────────
# WIDGETS HELPERS
# ──────────────────────────────────────────────────────────────

class HLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER}; border: none;")


class SectionTitle(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {CYAN_DIM};
            font-size: 10px;
            font-family: {MONO};
            letter-spacing: 3px;
            padding: 8px 0 4px 0;
        """)


# ──────────────────────────────────────────────────────────────
# MAIN WINDOW
# ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.pause = True
        self.forme_selectionnee = None
        self.grille = Grille(5, 5, 10)
        self.police_scientifique = QFont("Consolas", 13)
        self.resize(1280, 720)
        self.setWindowTitle("FLUID DYNAMICS SIMULATOR")
        self.setStyleSheet(APP_STYLE)

        self.centre = QWidget()
        self.setCentralWidget(self.centre)
        self.layout_principal = QHBoxLayout(self.centre)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # ── Scene 3D ──────────────────────────────────────────
        self.scene_containerScene = QWidget()
        self.scene_containerScene.setStyleSheet(f"background:{BG};")
        self.scene_layoutScene3D = QVBoxLayout(self.scene_containerScene)
        self.scene_layoutScene3D.setContentsMargins(0, 0, 0, 0)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.layout_principal.addWidget(self.scene_containerScene, stretch=3)

        # ── Stack panneau / édition ───────────────────────────
        self.stack = QStackedWidget()
        self.forme_en_scene = None

        # ══════════════════════════════════════════════════════
        # PANNEAU PRINCIPAL
        # ══════════════════════════════════════════════════════
        self.panneau = QWidget()
        self.panneau.setFixedWidth(320)
        self.panneau.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        self.layout_controles = QVBoxLayout(self.panneau)
        self.layout_controles.setContentsMargins(18, 16, 18, 16)
        self.layout_controles.setSpacing(4)

        # ── Header ────────────────────────────────────────────
        header_row = QHBoxLayout()
        title_lbl = QLabel("FLUID SIM")
        title_lbl.setStyleSheet(f"""
            color: {CYAN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        self.status_dot = QLabel("◉ IDLE")
        self.status_dot.setStyleSheet(f"""
            color: {TEXT2};
            font-size: 11px;
            letter-spacing: 2px;
        """)
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(self.status_dot)
        self.layout_controles.addLayout(header_row)
        self.layout_controles.addWidget(HLine())
        self.layout_controles.addSpacing(4)

        # ── Boutons Run / Reset ───────────────────────────────
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

        # ── Boutons formes ────────────────────────────────────
        self.layout_controles.addWidget(SectionTitle("OBSTACLES"))

        self.formesGeometriqueLigneDuHaut = QHBoxLayout()
        self.formesGeometriqueLigneDuHaut.setSpacing(6)
        self.formesGeometriqueLigneDuBas  = QHBoxLayout()
        self.formesGeometriqueLigneDuBas.setSpacing(6)

        formes_config = [
            ("realSphere.png", "sphere",   "red", self.formesGeometriqueLigneDuHaut),
            ("prisme.png",     "prisme",   "red", self.formesGeometriqueLigneDuHaut),
            ("cube.png",       "cube",     "red", self.formesGeometriqueLigneDuHaut),
            ("cylindre.png",   "cylindre", "red", self.formesGeometriqueLigneDuBas),
            ("Pyramide.png",   "pyramide", "red", self.formesGeometriqueLigneDuBas),
            ("fleche.png",     "fleche",   "red", self.formesGeometriqueLigneDuBas),
        ]

        for image, forme, couleur, ligne in formes_config:
            btn = QPushButton("")
            btn.setIcon(QPixmap(image))
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
            btn.clicked.connect(lambda checked, f=forme: self.ouvrir_panneau_forme(f))
            ligne.addWidget(btn)

        self.layout_controles.addLayout(self.formesGeometriqueLigneDuHaut)
        self.layout_controles.addSpacing(6)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuBas)
        self.layout_controles.addSpacing(4)
        self.layout_controles.addWidget(HLine())

        # ── Sliders paramètres ────────────────────────────────
        self.layout_controles.addWidget(SectionTitle("PARAMÈTRES FLUIDE"))

        self.texte_temperature, self.slider_temperature = self.creer_bloc("Température", 0, 30,    "°C")
        self.layout_controles.addSpacing(6)
        self.texte_viscous,     self.slider_viscous     = self.creer_bloc("Viscosité",   0, 1000,  "mPa")
        self.layout_controles.addSpacing(6)
        self.texte_pression,    self.slider_pression    = self.creer_bloc("Pression",    0, 301.4, "kPa", 10)
        self.layout_controles.addSpacing(6)
        self.texte_vitesse,     self.slider_vitesse     = self.creer_bloc("Vitesse",     0, 100,   "m/s")
        self.layout_controles.addStretch()

        # ══════════════════════════════════════════════════════
        # PANNEAU ÉDITION FORME
        # ══════════════════════════════════════════════════════
        self.scene2_container = QWidget()
        self.scene2_container.setFixedWidth(320)
        self.scene2_container.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        self.scene2_layout = QVBoxLayout(self.scene2_container)
        self.scene2_layout.setContentsMargins(18, 16, 18, 16)
        self.scene2_layout.setSpacing(6)

        # Retour
        btn_back = QPushButton("← RETOUR")
        btn_back.setFixedHeight(38)
        btn_back.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(btn_back)
        self.scene2_layout.addWidget(HLine())

        # Nom forme
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

        # Sliders dynamiques forme
        self.layout_sliders_forme = QVBoxLayout()
        self.layout_sliders_forme.setSpacing(8)
        self.scene2_layout.addLayout(self.layout_sliders_forme)
        self.sliders_forme = {}

        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addWidget(SectionTitle("POSITION"))

        # Sliders XYZ
        self.sliders_xyz = {}
        for axe, max_val in zip(["X", "Y", "Z"], [self.grille.x, self.grille.y, self.grille.z]):
            row = QHBoxLayout()
            row.setSpacing(10)

            axe_lbl = QLabel(axe)
            axe_lbl.setFixedWidth(16)
            axe_lbl.setStyleSheet(f"color:{CYAN}; font-size:13px; font-weight:bold;")

            slider = QSlider(Qt.Horizontal)
            slider.setRange(1, int(max_val * 100))
            slider.setValue(100)

            label_axe = QLabel("0.01")
            label_axe.setFixedWidth(42)
            label_axe.setFont(self.police_scientifique)
            label_axe.setStyleSheet(f"color:{TEXT}; font-size:13px;")

            slider.valueChanged.connect(lambda v, l=label_axe, a=axe.lower(): l.setText(f"{v/100:.2f}"))

            row.addWidget(axe_lbl)
            row.addWidget(slider)
            row.addWidget(label_axe)
            self.scene2_layout.addLayout(row)
            self.sliders_xyz[axe.lower()] = slider

        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addSpacing(6)

        # Confirmer / Supprimer
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
        self.scene2_layout.addStretch()

        # ── Stack final ───────────────────────────────────────
        self.stack.addWidget(self.panneau)
        self.stack.addWidget(self.scene2_container)
        self.layout_principal.addWidget(self.stack)

        # ── Paramètres formes (identique) ─────────────────────
        self.parametres_formes = {
            "sphere":   [("rayon", 1, 3)],
            "cube":     [("c", 1, 3)],
            "cylindre": [("rayon", 1, 3), ("h", 1, 3)],
            "prisme":   [("l", 1, 3), ("w", 1, 3), ("h", 1, 3)],
            "pyramide": [("h", 1, 3)],
            "fleche":   [("l", 1, 3), ("w", 1, 3)],
        }

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

    # ══════════════════════════════════════════════════════════
    # MÉTHODES — identiques à ton original
    # ══════════════════════════════════════════════════════════

    def generer_sliders_forme(self, nom_forme):
        self.sliders_forme.clear()
        while self.layout_sliders_forme.count():
            item = self.layout_sliders_forme.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for param, min_val, max_val in self.parametres_formes.get(nom_forme, []):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setSpacing(10)

            param_lbl = QLabel(param.upper())
            param_lbl.setFixedWidth(52)
            param_lbl.setStyleSheet(f"color:{TEXT2}; font-size:12px; letter-spacing:1px;")

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

    def creer_bloc(self, nom, min_val, max_val, unite="", facteur=1):
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

    def ouvrir_panneau_forme(self, nom_forme):
        self.forme_selectionnee = nom_forme
        self.label_forme_choisie.setText(nom_forme.upper())

        for slider in self.sliders_xyz.values():
            slider.setValue(100)

        self.generer_sliders_forme(nom_forme)

        default_valeurs = {param: min_val for param, min_val, max_val in self.parametres_formes.get(nom_forme, [])}
        self.forme_en_scene = self.scene.ajouter_forme_temporaire(nom_forme, default_valeurs)

        for slider in self.sliders_forme.values():
            try:
                slider.valueChanged.disconnect()
            except TypeError:
                pass
            slider.valueChanged.connect(self.mettre_a_jour_dimensions)

        self.stack.setCurrentIndex(1)

    def confirmer_forme(self):
        self.stack.setCurrentIndex(0)

    def supprimer_forme(self):
        print("in")
        if self.forme_en_scene is not None:
            print("out")
            self.scene.supprimer(self.scene.acteur_current)
        self.stack.setCurrentIndex(0)

    def mettre_a_jour_dimensions(self):
        if self.forme_en_scene is None:
            return
        valeurs = {nom: slider.value() / 100 for nom, slider in self.sliders_forme.items()}
        self.scene.acteur_current = self.forme_en_scene
        self.scene.changer_dimensions_dict(valeurs)

    def update_value(self, label, value, unite, facteur):
        valeur_reelle = value / facteur
        if facteur > 1:
            label.setText(f"{valeur_reelle:.2f} {unite}")
        else:
            label.setText(f"{int(valeur_reelle)} {unite}")

    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()

    def animerRun(self):
        if not self.pause:
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
        else:
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
            self.timer.start(1000 // 30)
        self.pause = not self.pause

    def animerReset(self):
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

        self.scene.plotter.close()
        self.scene_layoutScene3D.removeWidget(self.scene.plotter)
        self.scene.plotter.deleteLater()

        self.grille = Grille(5, 5, 10)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)

        self.slider_temperature.setValue(0)
        self.slider_viscous.setValue(0)
        self.slider_pression.setValue(0)
        self.slider_vitesse.setValue(0)
        print()