from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QTimer
import random

class fondEtoile(QWidget):
    def __init__(self, nb_etoiles=200, nb_fusees=3):
        super().__init__()

        # Génération des étoiles
        self.etoiles = []
        for _ in range(nb_etoiles):
            self.etoiles.append({
                "x": random.random(),
                "y": random.random(),
                "taille": random.randint(1,3),
                "v": random.uniform(0.0005, 0.002)  # vitesse relative
            })

        # Génération des fusées
        self.fusees = []
        for _ in range(nb_fusees):
            self.fusees.append({
                "x": random.random(),
                "y": random.random()/2,  # commencer dans la moitié haute
                "vx": random.uniform(0.002, 0.006),
                "vy": random.uniform(0.001, 0.003),
                "longueur": random.randint(20, 50)
            })

        # Timer pour animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(30)  # 30 ms ~ 33 FPS

    def tick(self):
        self.update_positions()
        self.update()  # redessine le widget

    def update_positions(self):
        # mettre à jour les étoiles
        for e in self.etoiles:
            e["y"] += e["v"]
            if e["y"] > 1.0:
                e["y"] = 0
                e["x"] = random.random()

        # mettre à jour les fusées
        for f in self.fusees:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            if f["x"] > 1.0 or f["y"] > 1.0:
                f["x"] = 0
                f["y"] = random.random()/2
                f["vx"] = random.uniform(0.002, 0.006)
                f["vy"] = random.uniform(0.001, 0.003)
                f["longueur"] = random.randint(20,50)

    def paintEvent(self, event):
        painter = QPainter(self)

        # fond spatial
        painter.fillRect(self.rect(), QColor(10, 15, 30))

        largeur = self.width()
        hauteur = self.height()

        # dessiner étoiles
        painter.setPen(QColor(220, 220, 255))
        for e in self.etoiles:
            px = int(e["x"] * largeur)
            py = int(e["y"] * hauteur)
            painter.drawEllipse(px, py, e["taille"], e["taille"])

        # dessiner fusées / comètes
        painter.setPen(QColor(255, 200, 50))
        for f in self.fusees:
            px = int(f["x"] * largeur)
            py = int(f["y"] * hauteur)
            # traînée
            painter.drawLine(px, py, px - int(f["vx"]*largeur*f["longueur"]), py - int(f["vy"]*hauteur*f["longueur"]))
            # tête de la fusée
            painter.drawEllipse(px, py, 3, 3)