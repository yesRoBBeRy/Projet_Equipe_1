from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QMainWindow, QWidget, QSlider, QLabel, QPushButton
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

        centre = fondEtoile(self.height(), self.width())
        self.setCentralWidget(centre)

        layout_principal = QHBoxLayout(centre)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(25)

        # scène3D
        scene_containerScene = QWidget()

        scene_layoutScene3D = QVBoxLayout(scene_containerScene)

        self.scene = Scene3D(scene_containerScene, self.grille)

        scene_layoutScene3D.addWidget(self.scene.plotter)

        layout_principal.addWidget(scene_containerScene, stretch=3)

        # panneau de contrôle
        panneau = QWidget()

        layout_controles = QVBoxLayout(panneau)

        layout_controles.setSpacing(10)

        def creer_bloc(nom, min_val, max_val, unite="", facteur=1):
            bloc = QVBoxLayout()

            texte = QLabel(nom)
            texte.setFont(police_scientifique)
            ligne = QHBoxLayout()
            label_valeur = QLabel(str(min_val) + " " + unite)

            label_valeur.setFont(police_scientifique)

            ligne.addWidget(texte)
            ligne.addStretch()
            ligne.addWidget(label_valeur)

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

        boutons = QHBoxLayout()

        boutons.setSpacing(10)

        boutonRun = QPushButton("Run")
        boutonPause = QPushButton("Pause")
        boutonReprendre = QPushButton("Reprendre")

        boutons.addWidget(boutonRun)
        boutons.addWidget(boutonPause)
        boutons.addWidget(boutonReprendre)

        boutonRun.clicked.connect(self.animerRun)
        boutonPause.clicked.connect(self.animerPause)
        boutonReprendre.clicked.connect(self.animerReprendre)

        # TODO les formes a mettre

        formesGeometrique = QHBoxLayout()
        boutonCercle = QPushButton("Cercle")
        boutonCercle.setFixedSize(130, 130)  # taille du cercle
        boutonCercle.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)

        boutonRectangle = QPushButton("Rectangle")
        boutonRectangle.setFixedSize(130, 130)
        boutonRectangle.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)

        boutonCarre = QPushButton("Carre")
        boutonCarre.setFixedSize(130, 130)
        boutonCarre.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)



        formesGeometrique.addWidget(boutonCercle)
        formesGeometrique.addWidget(boutonRectangle)
        formesGeometrique.addWidget(boutonCarre)

        layout_controles.addLayout(boutons)
        layout_controles.addLayout(formesGeometrique)
        self.texte_temperature, self.slider_temperature = creer_bloc("Temperature", 0, 30, "°C")
        self.texte_viscous, self.slider_viscous = creer_bloc("Viscous", 0, 1000)
        self.texte_pression, self.slider_pression = creer_bloc("Pression", 101.4, 301.4, "kPa", 10)
        self.texte_vitesse, self.slider_vitesse = creer_bloc("Vitesse", 0, 100, "m/s")

        layout_controles.addStretch()

        layout_principal.addWidget(panneau, stretch=1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

    def update_value(self, label, value, unite, facteur):
        valeur_reelle = value / facteur
        label.setText(f"{valeur_reelle} {unite}")

    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()