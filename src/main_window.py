from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.grille = Grille(25,25,25)

        self.resize(800, 600)

        centre = QWidget()
        self.setCentralWidget(centre)

        layout = QHBoxLayout(centre)

        self.scene = Scene3D(centre, self.grille)

        layout.addWidget(self.scene.plotter)

        self.scene.plotter.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1000//30)

    def update(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()