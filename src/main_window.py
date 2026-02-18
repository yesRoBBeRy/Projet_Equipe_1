from PySide6.QtWidgets import QMainWindow, QVBoxLayout

from src.scene_3D import Scene3D


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.scene = Scene3D(self)

        layout.addWidget(self.scene.plotter)

        self.setLayout(layout)