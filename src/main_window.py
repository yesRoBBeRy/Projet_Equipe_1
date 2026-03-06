from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QMainWindow, QWidget,
    QPushButton, QSlider, QLabel
)

from fondEtoile import fondEtoile
from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.grille = Grille(5, 5, 10)

        police_scientifique = QFont("Consolas", 12)  # monospace, taille 12

        self.resize(1200, 650)

        centre = fondEtoile()
        self.setCentralWidget(centre)

        # ===== STYLE AEROSPACE =====
        self.setStyleSheet("""
        QMainWindow {
            background-color: #0b0f1a;
            font-family: Roboto Mono;
            font-size: 12pt;
        }

        QLabel {
            color: #cfd8ff;
            font-family: Consolas;
            font-size: 12pt;
        }

        QPushButton {
            background-color: #1c2238;
            color: white;
            border: 1px solid #3b4a7a;
            padding: 6px;
            font-family: Consolas;
            font-size: 12pt;
        }

        QPushButton:hover {
            background-color: #2b3560;
        }

        QSlider::groove:horizontal {
            background: #2a3355;
            height: 6px;
        }

        QSlider::handle:horizontal {
            background: #6fa8ff;
            width: 12px;
        }
        """)

        layout_principal = QHBoxLayout(centre)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(25)

        # ===== SCENE 3D =====
        scene_container = QWidget()
        scene_container.setStyleSheet("""
        background-color: black;
        border: 3px solid black;
        """)

        scene_layout = QVBoxLayout(scene_container)

        self.scene = Scene3D(scene_container, self.grille)

        scene_layout.addWidget(self.scene.plotter)

        layout_principal.addWidget(scene_container, stretch=3)

        # ===== PANNEAU CONTROLES =====
        panneau = QWidget()
        layout_controles = QVBoxLayout(panneau)
        layout_controles.setSpacing(40)

        def creer_bloc(nom, min_val, max_val, unite="", facteur=1):
            bloc = QVBoxLayout()

            # ligne titre + valeur
            ligne = QHBoxLayout()
            label_nom = QLabel(nom)
            label_valeur = QLabel(str(min_val) + " " + unite)

            # Appliquer police scientifique au label de valeur
            label_valeur.setFont(police_scientifique)

            ligne.addWidget(label_nom)
            ligne.addStretch()
            ligne.addWidget(label_valeur)

            # bouton
            bouton = QPushButton(nom)
            bouton.setFont(police_scientifique)  # police scientifique sur bouton

            # slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * facteur), int(max_val * facteur))

            slider.valueChanged.connect(
                lambda v, l=label_valeur, u=unite, f=facteur:
                self.update_value(l, v, u, f)
            )

            bloc.addLayout(ligne)
            bloc.addWidget(bouton)
            bloc.addWidget(slider)

            layout_controles.addLayout(bloc)

            return bouton, slider

        # ===== PARAMETRES =====

        self.btn_temperature, self.slider_temperature = creer_bloc(
            "Temperature", 0, 30, "°C"
        )

        self.btn_viscous, self.slider_viscous = creer_bloc(
            "Viscous", 0, 1000
        )

        self.btn_pression, self.slider_pression = creer_bloc(
            "Pression", 101.4, 301.4, "kPa", 10
        )

        self.btn_vitesse, self.slider_vitesse = creer_bloc(
            "Vitesse", 0, 100, "m/s"
        )

        layout_controles.addStretch()

        layout_principal.addWidget(panneau, stretch=1)

        # ===== TIMER =====
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // 30)

    def update_value(self, label, value, unite, facteur):

        valeur_reelle = value / facteur
        label.setText(f"{valeur_reelle} {unite}")

    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()