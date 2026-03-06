from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QTimer
import random
import math


class fondEtoile(QWidget):
    def __init__(self, nb_etoiles=200, nb_fusees=3):
        super().__init__()

        # ==== étoiles ====
        self.etoiles = []
        for _ in range(nb_etoiles):
            self.etoiles.append({
                "x": random.random(),  # position x [0,1]
                "y": random.random(),  # position y [0,1]
                "taille": random.randint(1, 3),
                "v": random.uniform(0.0005, 0.002)  # vitesse verticale
            })

        # ==== fusées ====
        self.fusees = []
        for _ in range(nb_fusees):
            self.fusees.append({
                "x": random.random(),
                "y": random.random() / 2,
                "vx": random.uniform(0.002, 0.006),
                "vy": random.uniform(0.001, 0.003),
                "longueur": random.randint(20, 50)
            })

        # ==== timer pour animation ====
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)  # 30 ms ≈ 33 FPS

    def tick(self):
        self.update_positions()
        self.update()  # redessine le widget

    def update_positions(self):
        # étoiles
        for e in self.etoiles:
            e["y"] += e["v"]
            if e["y"] > 1.0:
                e["y"] = 0
                e["x"] = random.random()

        # fusées
        for f in self.fusees:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            if f["x"] > 1.0 or f["y"] > 1.0:
                f["x"] = 0
                f["y"] = random.random() / 2
                f["vx"] = random.uniform(0.002, 0.006)
                f["vy"] = random.uniform(0.001, 0.003)
                f["longueur"] = random.randint(20, 50)

    def paintEvent(self, event):
        painter = QPainter(self)

        # fond spatial
        painter.fillRect(self.rect(), QColor(10, 15, 30))

        largeur = self.width()
        hauteur = self.height()

        # ==== dessiner étoiles ====
        painter.setPen(QColor(220, 220, 255))
        for e in self.etoiles:
            px = int(e["x"] * largeur)
            py = int(e["y"] * hauteur)
            painter.drawEllipse(px, py, e["taille"], e["taille"])

        # ==== dessiner fusées avec traînée remplie ====
        for f in self.fusees:
            px0 = int(f["x"] * largeur)
            py0 = int(f["y"] * hauteur)
            px1 = int(px0 - f["vx"] * largeur * f["longueur"])
            py1 = int(py0 - f["vy"] * hauteur * f["longueur"])

            # traînée jaune semi-transparente
            painter.setBrush(QColor(255, 220, 50, 180))
            painter.setPen(QColor(255, 220, 50, 180))

            # calcul angle et longueur
            dx = px0 - px1
            dy = py0 - py1
            longueur = math.hypot(dx, dy)
            angle = math.degrees(math.atan2(dy, dx))

            painter.save()
            painter.translate(px1, py1)
            painter.rotate(angle)
            painter.drawRect(0, -2, int(longueur), 4)  # rectangle traînée
            painter.restore()

            # tête de la fusée
            painter.setBrush(QColor(255, 255, 255))
            painter.setPen(QColor(255, 255, 255))
            painter.drawEllipse(px0, py0, 4, 4)