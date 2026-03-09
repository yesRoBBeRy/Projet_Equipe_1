from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QMainWindow, QWidget, QSlider, QLabel
)

from fondEtoile import fondEtoile
from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.grille = Grille(5, 5, 10)

        police_scientifique = QFont("Consolas", 12)  # monospace, taille 12


        self.resize(1200,650)

        centre = fondEtoile()
        self.setCentralWidget(centre)





        layout_principal = QHBoxLayout(centre)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(25)


        scene_container = QWidget()


        scene_layout = QVBoxLayout(scene_container)

        self.scene = Scene3D(scene_container, self.grille)

        scene_layout.addWidget(self.scene.plotter)

        layout_principal.addWidget(scene_container, stretch=3)


        panneau = QWidget()
        layout_controles = QVBoxLayout(panneau)
        layout_controles.setSpacing(40)

        def creer_bloc(nom, min_val, max_val, unite="", facteur=1):
            bloc = QVBoxLayout()


            ligne = QHBoxLayout()
            label_nom = QLabel(nom)
            label_valeur = QLabel(str(min_val) + " " + unite)


            label_valeur.setFont(police_scientifique)

            ligne.addWidget(label_nom)
            ligne.addStretch()
            ligne.addWidget(label_valeur)


            texte = QLabel(nom)
            texte.setFont(police_scientifique)


            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * facteur), int(max_val * facteur))

            slider.valueChanged.connect(
                lambda v, l=label_valeur, u=unite, f=facteur:
                self.update_value(l, v, u, f)
            )

            bloc.addLayout(ligne)
            bloc.addWidget(texte)
            bloc.addWidget(slider)

            layout_controles.addLayout(bloc)

            return texte, slider



        self.texte_temperature, self.slider_temperature = creer_bloc(
            "Temperature", 0, 30, "°C"
        )

        self.texte_viscous, self.slider_viscous = creer_bloc(
            "Viscous", 0, 1000
        )

        self.texte_pression, self.slider_pression = creer_bloc(
            "Pression", 101.4, 301.4, "kPa", 10
        )

        self.texte_vitesse, self.slider_vitesse = creer_bloc(
            "Vitesse", 0, 100, "m/s"
        )

        layout_controles.addStretch()

        layout_principal.addWidget(panneau, stretch=1)


        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000 // 30)

    def update_value(self, label, value, unite, facteur):

        valeur_reelle = value / facteur
        label.setText(f"{valeur_reelle} {unite}")

    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()