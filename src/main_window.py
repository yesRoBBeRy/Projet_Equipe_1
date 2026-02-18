from PySide6.QtWidgets import QMainWindow, QVBoxLayout



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(self.scene.plotter)

        self.setLayout(layout)