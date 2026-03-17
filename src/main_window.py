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
        bouton_reprendre = QPushButton("Reprendre")

        boutons.addWidget(boutonRun)
        boutons.addWidget(boutonPause)
        boutons.addWidget(bouton_reprendre)

        #boutonRun.clicked.connect(self.animerRun)
        #boutonPause.clicked.connect(self.animerPause)
        #boutonReprendre.clicked.connect(self.animerReprendre)

        formes_geometrique = QHBoxLayout()
        bouton_sphere = QPushButton("Cercle")
        bouton_sphere.setFixedSize(130, 130)  # taille du cercle
        bouton_sphere.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)

        bouton_prisme = QPushButton("Rectangle")
        bouton_prisme.setFixedSize(130, 130)
        bouton_prisme.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)

        bouton_cube = QPushButton("Carre")
        bouton_cube.setFixedSize(130, 130)
        bouton_cube.setStyleSheet("""
        QPushButton {
            border-radius: 25px;  
            border: 10px solid black;
            
        }
        QPushButton:hover {
            background-color: lightgrey;
        }
        """)

        bouton_sphere.clicked.connect(self.add_sphere)
        bouton_cube.clicked.connect(self.add_cube)
        bouton_prisme.clicked.connect(self.add_prisme)

        formes_geometrique.addWidget(bouton_sphere)
        formes_geometrique.addWidget(bouton_prisme)
        formes_geometrique.addWidget(bouton_cube)

        layout_controles.addLayout(boutons)
        layout_controles.addLayout(formes_geometrique)
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

    def add_sphere(self):
        # TODO: Logique du choix des dimensions de la sphère
        rayon = 1

        self.scene.add_sphere(rayon)

    def add_prisme(self):
        # TODO: Logique du choix des dimension du prisme
        h = 1
        l = 1

        self.scene.add_prisme(h, l)

    def add_cylindre(self):
        # TODO: Logique du choix des dimension du prisme
        rayon = 1
        h = 1

        self.scene.add_cylindre(rayon, h)

    def add_cube(self):
        # TODO: Logique du choix des dimensions du cube
        c = 1

        self.scene.add_cube(c)