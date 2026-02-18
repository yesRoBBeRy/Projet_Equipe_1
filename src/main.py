from PySide6.QtWidgets import QApplication
import sys

from src.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()