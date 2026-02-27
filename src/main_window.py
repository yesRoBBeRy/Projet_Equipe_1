from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget, QPushButton

from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.grille = Grille(50,50,100)

        self.resize(800, 600)

        centre = QWidget()
        self.setCentralWidget(centre)

        layout = QHBoxLayout(centre)

        self.scene = Scene3D(centre, self.grille)
        self.btn = QPushButton("Sphere")
        self.btn.clicked.connect(self.scene.add_sphere)

        layout.addWidget(self.scene.plotter)
        layout.addWidget(self.btn)

        self.scene.plotter.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000//30)

    def update(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()