import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QBrush, QPolygon


class fondEtoile(QWidget):
    def __init__(self, hauteur, largeur):
        super().__init__()
        self.setFixedSize(largeur, hauteur)

        self.etoilesG = [(random.randint(0, largeur), random.randint(0, hauteur),
                          random.randint(1, 2), random.randint(-1, 1)) for _ in range(50)]
        self.etoilesD = [(random.randint(0, largeur), random.randint(0, hauteur),
                          random.randint(-2, -1), random.randint(-1, 1)) for _ in range(50)]
        self.etoilesHB = [(random.randint(0, largeur), hauteur,
                           random.randint(1, 2), random.randint(1, 3)) for _ in range(50)]

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_etoiles)
        self.timer.start(30)

    def animerEtoile(self, etoiles):
        for i in range(len(etoiles)):
            x, y, vx, vy = etoiles[i]
            x += vx
            y += vy

            if y > self.height():
                y = random.randint(0, self.height())
                x = random.randint(0, self.width())
            if x > self.width():
                x = random.randint(0, self.width())
                y = random.randint(0, self.height())

            etoiles[i] = (x, y, vx, vy)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(15, 30, 60))
        painter.setBrush(QBrush(QColor("white")))

        for x, y, vx, vy in self.etoilesG:
            painter.drawEllipse(x, y, 2, 2)
        for x, y, vx, vy in self.etoilesD:
            painter.drawEllipse(x, y, 2, 2)
        for x, y, vx, vy in self.etoilesHB:
            painter.drawEllipse(x, y, 2, 2)

    def update_etoiles(self):
        self.animerEtoile(self.etoilesG)
        self.animerEtoile(self.etoilesD)
        self.animerEtoile(self.etoilesHB)

def draw_star(painter, x, y, size=1):
    points = [
        QPoint(x, y - size),
        QPoint(x + size // 2, y + size),
        QPoint(x - size, y // 2),
        QPoint(x + size, y // 2),
        QPoint(x - size // 2, y + size)
    ]
    polygon = QPolygon(points)
    painter.drawPolygon(polygon)