from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille
from PySide6.QtWidgets import QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QStackedWidget
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.pause = True
        self.forme_selectionnee = None
        self.grille = Grille(5, 5, 10)
        self.police_scientifique = QFont("Consolas", 12)
        self.resize(1200, 650)

        self.centre = QWidget()
        self.setCentralWidget(self.centre)
        self.layout_principal = QHBoxLayout(self.centre)

        # --- Scene 3D ---
        self.scene_containerScene = QWidget()
        self.scene_layoutScene3D = QVBoxLayout(self.scene_containerScene)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.layout_principal.addWidget(self.scene_containerScene, stretch=3)

        self.scene.forme.connect(self.recevoir_forme)

        # --- Stack pour panneau / édition ---
        self.stack = QStackedWidget()
        self.forme_en_scene = None

        # --- Panneau principal ---
        self.panneau = QWidget()
        self.layout_controles = QVBoxLayout(self.panneau)

        self.boutons = QHBoxLayout()
        self.boutonRun = QPushButton("Commencer la simulation")
        self.bouton_reset = QPushButton("Reset")
        self.boutons.addWidget(self.boutonRun)
        self.boutons.addWidget(self.bouton_reset)
        self.boutonRun.clicked.connect(self.animerRun)
        self.bouton_reset.clicked.connect(self.animerReset)
        self.layout_controles.addLayout(self.boutons)

        # --- Boutons formes ---
        self.formesGeometriqueLigneDuHaut = QHBoxLayout()
        self.formesGeometriqueLigneDuBas = QHBoxLayout()

        formes_config = [
            ("realSphere.png", "sphere", "red", self.formesGeometriqueLigneDuHaut),
            ("prisme.png", "prisme", "red", self.formesGeometriqueLigneDuHaut),
            ("cube.png", "cube", "red", self.formesGeometriqueLigneDuHaut),
            ("cylindre.png", "cylindre", "red", self.formesGeometriqueLigneDuBas),
            ("Pyramide.png", "pyramide", "red", self.formesGeometriqueLigneDuBas),
            ("fleche.png", "fleche", "red", self.formesGeometriqueLigneDuBas),
        ]

        for image, forme, couleur, ligne in formes_config:
            btn = QPushButton("")
            btn.setIcon(QPixmap(image))
            btn.setIconSize(QSize(100, 100))
            btn.setFixedSize(130, 130)
            btn.setStyleSheet(f"""
                QPushButton {{ border-radius: 25px; }}
                QPushButton:hover {{ background-color: {couleur}; }}
            """)
            btn.clicked.connect(lambda checked, f=forme: self.ouvrir_panneau_forme(f))
            ligne.addWidget(btn)

        self.layout_controles.addLayout(self.formesGeometriqueLigneDuHaut)
        self.layout_controles.addSpacing(10)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuBas)
        self.layout_controles.addSpacing(10)


        self.texte_temperature, self.slider_temperature = self.creer_bloc("Temperature", 0, 30, "°C")
        self.layout_controles.addSpacing(10)
        self.texte_viscous, self.slider_viscous = self.creer_bloc("Viscous", 0, 1000)
        self.layout_controles.addSpacing(10)
        self.texte_pression, self.slider_pression = self.creer_bloc("Pression", 0, 301.4, "kPa", 10)
        self.layout_controles.addSpacing(10)
        self.texte_vitesse, self.slider_vitesse = self.creer_bloc("Vitesse", 0, 100, "m/s")
        self.layout_controles.addStretch()


        self.scene2_container = QWidget()
        self.scene2_layout = QVBoxLayout(self.scene2_container)

        self.label_forme_choisie = QLabel("Forme")
        self.label_forme_choisie.setFont(self.police_scientifique)
        self.scene2_layout.addWidget(self.label_forme_choisie)

        self.layout_sliders_forme = QVBoxLayout()
        self.scene2_layout.addLayout(self.layout_sliders_forme)
        self.sliders_forme = {}

        self.sliders_xyz = {}
        for axe, max_val in zip(["x", "y", "z"], [self.grille.x, self.grille.y, self.grille.z]):
            ligne = QHBoxLayout()
            label_axe = QLabel(f"{axe}: 0.01")
            label_axe.setFont(self.police_scientifique)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(1, int(max_val * 100))
            slider.setValue(100)
            slider.valueChanged.connect(lambda v, l=label_axe, a=axe: self.update_slider_position(v, l, a))
            ligne.addWidget(QLabel(axe))
            ligne.addWidget(slider)
            ligne.addWidget(label_axe)
            self.scene2_layout.addLayout(ligne)
            self.sliders_xyz[axe] = slider

        self.bouton_confirmer = QPushButton("Confirmer")
        self.bouton_confirmer.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(self.bouton_confirmer)

        self.bouton_supprimer = QPushButton("Supprimer")
        self.bouton_supprimer.clicked.connect(self.supprimer_forme)
        self.scene2_layout.addWidget(self.bouton_supprimer)
        self.scene2_layout.addStretch()


        self.stack.addWidget(self.panneau)
        self.stack.addWidget(self.scene2_container)
        self.layout_principal.addWidget(self.stack, stretch=3)


        self.parametres_formes = {
            "sphere": [("rayon", 1, 3)],
            "cube": [("c", 1, 3)],
            "cylindre": [("rayon", 1, 3), ("h", 1, 3)],
            "prisme": [("l", 1, 3), ("w", 1, 3), ("h", 1, 3)],
            "pyramide": [("h", 1, 3)],
            "fleche": [("l", 1, 3), ("w", 1, 3)],
        }

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

    def update_slider_position(self, v, l, a,):
        if self.forme_en_scene not in self.scene.pos_current:
            return
        l.setText(f"{a}: {v / 100:.2f}")
        pos = v/100
        x, y, z = self.scene.pos_current[self.forme_en_scene]
        if a == "x":
            self.scene.deplacement(pos,y, z)
        elif a == "y":
            self.scene.deplacement(x, pos, z)
        elif a == "z":
            self.scene.deplacement(x, y, pos)


    def generer_sliders_forme(self, nom_forme):
        while self.layout_sliders_forme.count():
            item = self.layout_sliders_forme.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.sliders_forme.clear()

        for param, min_val, max_val in self.parametres_formes.get(nom_forme, []):
            container = QWidget()
            layout = QHBoxLayout(container)

            label = QLabel(f"{min_val:.2f}")
            label.setFont(self.police_scientifique)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(min_val * 100))

            slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v / 100:.2f}"))

            layout.addWidget(QLabel(param))
            layout.addWidget(slider)
            layout.addWidget(label)

            self.layout_sliders_forme.addWidget(container)
            self.sliders_forme[param] = slider



    def creer_bloc(self, nom, min_val, max_val, unite="", facteur=1):
        bloc = QVBoxLayout()
        texte = QLabel(nom)
        texte.setFont(self.police_scientifique)
        ligne = QHBoxLayout()
        label_valeur = QLabel(f"{min_val} {unite}")
        label_valeur.setFont(self.police_scientifique)
        ligne.addWidget(texte)
        ligne.addStretch()
        ligne.addWidget(label_valeur)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(min_val * facteur), int(max_val * facteur))
        slider.valueChanged.connect(
            lambda v, l=label_valeur, u=unite, f=facteur: self.update_value(l, v, u, f)
        )
        bloc.addLayout(ligne)
        bloc.addWidget(slider)
        self.layout_controles.addLayout(bloc)
        return texte, slider



    def ouvrir_panneau_forme(self, nom_forme):
        self.forme_selectionnee = nom_forme
        self.label_forme_choisie.setText(nom_forme.capitalize())


        for slider in self.sliders_xyz.values():
            slider.setValue(100)

        # Générer sliders forme
        self.generer_sliders_forme(nom_forme)

        # Créer une forme temporaire dans Scene3D
        default_valeurs = {param: min_val for param, min_val, max_val in self.parametres_formes.get(nom_forme, [])}
        self.forme_en_scene = self.scene.add_forme(nom_forme, default_valeurs)
        self.scene.acteur_current = self.forme_en_scene


        # Sliders modifient les dimensions en direct
        for slider in self.sliders_forme.values():
            try:
                slider.valueChanged.disconnect()
            except TypeError:
                pass
            slider.valueChanged.connect(self.mettre_a_jour_dimensions)

        self.stack.setCurrentIndex(1)



    def confirmer_forme(self):
        self.stack.setCurrentIndex(0)



    def supprimer_forme(self):
        if self.forme_en_scene is not None:
            self.scene.supprimer(self.scene.acteur_current)
        self.stack.setCurrentIndex(0)



    def mettre_a_jour_dimensions(self):
        if self.forme_en_scene is None:
            return
        valeurs = {nom: slider.value() / 100 for nom, slider in self.sliders_forme.items()}
        self.scene.acteur_current = self.forme_en_scene
        self.scene.changer_dimensions_dict(valeurs)



    def update_value(self, label, value, unite, facteur):
        valeur_reelle = value / facteur
        if facteur > 1:
            label.setText(f"{valeur_reelle:.2f} {unite}")
        else:
            label.setText(f"{int(valeur_reelle)} {unite}")



    def update_simulation(self):
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()


    def animerRun(self):
        if not self.pause:
            self.boutonRun.setStyleSheet("QPushButton { background-color: green; }")
            self.boutonRun.setText("Play")
            self.timer.stop()
        else:
            self.boutonRun.setStyleSheet("QPushButton { background-color: red; }")
            self.boutonRun.setText("Stop")
            self.timer.start(1000 // 30)
        self.pause = not self.pause


    def animerReset(self):
        self.timer.stop()
        self.pause = True
        self.boutonRun.setText("Commencer la simulation")
        self.boutonRun.setStyleSheet("QPushButton { background-color: white; }")

        self.scene.plotter.close()
        self.scene_layoutScene3D.removeWidget(self.scene.plotter)
        self.scene.plotter.deleteLater()

        self.grille = Grille(5, 5, 10)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)

        self.slider_temperature.setValue(0)
        self.slider_viscous.setValue(0)
        self.slider_pression.setValue(0)
        self.slider_vitesse.setValue(0)
        print()

    def recevoir_forme(self, acteur):
        if acteur is None:
            return

        self.forme_en_scene = acteur
        self.scene.acteur_current = acteur

        params = self.scene.parametres_formes.get(acteur)
        if params is None:
            return

        nom_forme = params["type"]
        self.label_forme_choisie.setText(nom_forme.capitalize())

        self.generer_sliders_forme(nom_forme)

        for nom, slider in self.sliders_forme.items():
            valeur = params["params"].get(nom, 1)
            slider.setValue(int(valeur * 100))

        if acteur in self.scene.pos_current:
            x, y, z = self.scene.pos_current[acteur]
            self.sliders_xyz["x"].setValue(int(x * 100))
            self.sliders_xyz["y"].setValue(int(y * 100))
            self.sliders_xyz["z"].setValue(int(z * 100))

        self.stack.setCurrentIndex(1)