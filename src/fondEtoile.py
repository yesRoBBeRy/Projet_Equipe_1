from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QBrush
from PySide6.QtCore import Qt
import random


class fondEtoile(QWidget):
    def __init__(self):
        super().__init__()

        self.etoiles = [(random.randint(0,1200 ), random.randint(0, 650)) for _ in range(100)]

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.fillRect(self.rect(), QColor(15, 30, 60))

        painter.setBrush(QBrush(QColor("white")))
        for x, y in self.etoiles:
            painter.drawEllipse(x, y, 2, 2)


