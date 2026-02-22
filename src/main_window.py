
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QWidget

from src.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(800, 600)

        centre = QWidget()
        self.setCentralWidget(centre)

        layout = QHBoxLayout(centre)

        self.scene = Scene3D(centre, self.grille)

        layout.addWidget(self.scene.plotter)

        self.scene.plotter.show()