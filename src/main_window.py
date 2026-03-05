from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget, QPushButton

from src.scene_3D import Scene3D
from src.grille import Grille


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.grille = Grille(5,5,10)

        self.resize(800, 600)

        central = QWidget()
        self.setCentralWidget(central)

        # Main horizontal layout
        mainLayout = QHBoxLayout(central)

        # Left and Right panels
        left = QWidget()
        right = QWidget()

        mainLayout.addWidget(left)
        mainLayout.addWidget(right)

        layoutLeft = QVBoxLayout(left)
        layoutRight = QVBoxLayout(right)

        # Scene on the left
        self.scene = Scene3D(left, self.grille)
        layoutLeft.addWidget(self.scene.plotter)

        # Button on the right
        self.button = QPushButton("Start")
        layoutRight.addWidget(self.button)

        self.scene.plotter.show()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update) # renamed
        self.timer.start(1000 // 30)

    def update(self):
        self.grille.update_valeurs()
        self.scene.update_scene()
        print("oenis")




