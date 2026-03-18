from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille




from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSlider
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.pause = True

        self.grille = Grille(5, 5, 10)

        self.police_scientifique = QFont("Consolas", 12)

        self.resize(1200, 650)

        self.centre = QWidget()
        self.setCentralWidget(self.centre)

        self.layout_principal = QHBoxLayout(self.centre)
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        self.layout_principal.setSpacing(25)

        self.scene_containerScene = QWidget()
        self.scene_layoutScene3D = QVBoxLayout(self.scene_containerScene)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.layout_principal.addWidget(self.scene_containerScene, stretch=3)

        self.panneau = QWidget()
        self.layout_controles = QVBoxLayout(self.panneau)
        self.layout_controles.setSpacing(10)

        def creer_bloc(nom, min_val, max_val, unite="", facteur=1):
            self.bloc = QVBoxLayout()
            self.texte = QLabel(nom)
            self.texte.setFont(self.police_scientifique)
            self.ligne = QHBoxLayout()
            self.label_valeur = QLabel(str(min_val) + " " + unite)
            self.label_valeur.setFont(self.police_scientifique)
            self.ligne.addWidget(self.texte)
            self.ligne.addStretch()
            self.ligne.addWidget(self.label_valeur)
            self.slider = QSlider(Qt.Horizontal)
            self.slider.setRange(int(min_val * facteur), int(max_val * facteur))
            self.slider.valueChanged.connect(
                lambda v, l=self.label_valeur, u=unite, f=facteur:
                self.update_value(l, v, u, f)
            )
            self.bloc.addLayout(self.ligne)
            self.bloc.addWidget(self.texte)
            self.bloc.addWidget(self.slider)
            self.layout_controles.addLayout(self.bloc)
            return self.texte, self.slider

        self.boutons = QHBoxLayout()
        self.boutons.setSpacing(10)

        self.boutonRun = QPushButton("Clique moi!")
        self.bouton_reset = QPushButton("Reset")

        self.boutons.addWidget(self.boutonRun)
        self.boutons.addWidget(self.bouton_reset)

        self.boutonRun.clicked.connect(self.animerRun)
        self.bouton_reset.clicked.connect(self.animerReset)

        self.formesGeometriqueLigneDuHaut = QHBoxLayout()

        self.image_sphere = QPixmap("realSphere.png")
        self.bouton_sphere = QPushButton("")
        self.bouton_sphere.setIcon(self.image_sphere)
        self.bouton_sphere.setIconSize(QSize(100, 100))
        self.bouton_sphere.setFixedSize(130, 130)
        self.bouton_sphere.setStyleSheet("""
            QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.image_rectangle = QPixmap("rectangle.png")
        self.bouton_prisme = QPushButton("")
        self.bouton_prisme.setIcon(self.image_rectangle)
        self.bouton_prisme.setIconSize(QSize(100, 100))
        self.bouton_prisme.setFixedSize(130, 130)
        self.bouton_prisme.setStyleSheet("""
             QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.image_carre = QPixmap("cube.png")
        self.bouton_cube = QPushButton("")
        self.bouton_cube.setIcon(self.image_carre)
        self.bouton_cube.setIconSize(QSize(100, 100))
        self.bouton_cube.setFixedSize(130, 130)
        self.bouton_cube.setStyleSheet("""
             QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.formesGeometriqueLigneDuHaut.addWidget(self.bouton_sphere)
        self.formesGeometriqueLigneDuHaut.addWidget(self.bouton_prisme)
        self.formesGeometriqueLigneDuHaut.addWidget(self.bouton_cube)

        self.formesGeometriqueLigneDuBas = QHBoxLayout()

        self.image_cylindre = QPixmap("cylindre.png")
        self.bouton_cylindre = QPushButton("")
        self.bouton_cylindre.setIcon(self.image_cylindre)
        self.bouton_cylindre.setIconSize(QSize(100, 100))
        self.bouton_cylindre.setFixedSize(130, 130)
        self.bouton_cylindre.setStyleSheet("""
             QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.bouton_sphere.clicked.connect(self.add_sphere)
        self.bouton_cube.clicked.connect(self.add_cube)
        self.bouton_prisme.clicked.connect(self.add_prisme)

        self.image_pyramide = QPixmap("prismeTriangulaire.png")
        self.bouton_pyramide = QPushButton("")
        self.bouton_pyramide.setIcon(self.image_pyramide)
        self.bouton_pyramide.setIconSize(QSize(100, 100))
        self.bouton_pyramide.setFixedSize(130, 130)
        self.bouton_pyramide.setStyleSheet("""
            QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.bouton_parralelogramme = QPushButton("")
        self.bouton_parralelogramme.setFixedSize(130, 130)
        self.bouton_parralelogramme.setStyleSheet("""
             QPushButton { border-radius: 25px; border: 6px solid black; }
            QPushButton:hover { background-color: orange; }
        """)

        self.formesGeometriqueLigneDuBas.addWidget(self.bouton_cylindre)
        self.formesGeometriqueLigneDuBas.addWidget(self.bouton_pyramide)
        self.formesGeometriqueLigneDuBas.addWidget(self.bouton_parralelogramme)

        self.layout_controles.addLayout(self.boutons)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuHaut)
        self.layout_controles.setSpacing(5)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuBas)

        self.texte_temperature, self.slider_temperature = creer_bloc("Temperature", 0, 30, "°C")
        self.texte_viscous, self.slider_viscous = creer_bloc("Viscous", 0, 1000)
        self.texte_pression, self.slider_pression = creer_bloc("Pression", 101.4, 301.4, "kPa", 10)
        self.texte_vitesse, self.slider_vitesse = creer_bloc("Vitesse", 0, 100, "m/s")

        self.layout_controles.addStretch()
        self.layout_principal.addWidget(self.panneau, stretch=1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

    def update_value(self, label, value, unite, facteur):
        valeur_reelle = value / facteur
        label.setText(f"{valeur_reelle} {unite}")

    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()

    def add_sphere(self):
        rayon = 1
        self.scene.add_sphere(rayon)

    def add_prisme(self):
        h = 1
        l = 2
        w = 3
        self.scene.add_prisme(h, l, w)

    def animerRun(self):
        if not self.pause:
            self.boutonRun.setStyleSheet("""
                QPushButton { background-color: green; }
            """)
            self.boutonRun.setText("Play")
            self.timer.stop()
        elif self.pause:
            self.boutonRun.setStyleSheet("""
                QPushButton { background-color: red; }
            """)
            self.boutonRun.setText("Stop")
            self.timer.start(1000 // 30)
        self.pause = not self.pause

    def add_cylindre(self):
        rayon = 1
        h = 1
        self.scene.add_cylindre(rayon, h)

    def animerReset(self):
        self.timer.stop()
        self.pause = True
        self.boutonRun.setText("Play")
        self.boutonRun.setStyleSheet("""
            QPushButton { background-color: green; }
        """)

        self.scene.plotter.close()
        self.scene_layoutScene3D.removeWidget(self.scene.plotter)
        self.scene.plotter.deleteLater()

        self.grille = Grille(5,5,10)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)

    def add_cube(self):
        c = 1
        self.scene.add_cube(c)

    def add_pyramide(self):
        self.scene.add_pyramide()