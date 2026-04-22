from src.Rendering_3D.scene_3D import Scene3D
from src.grille import Grille
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSlider, QPushButton, QStackedWidget, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap


# ── Palette de couleurs de l'interface ──────────────────────────────────────
BG       = "#050d1a"   # Fond principal (bleu très sombre)
SURFACE  = "#091525"   # Surface des éléments
PANEL    = "#071020"   # Fond du panneau latéral
BORDER   = "#0e2a45"   # Bordure subtile
BORDER2  = "#1a4060"   # Bordure accentuée
CYAN     = "#00d4ff"   # Couleur d'accent principale
CYAN_DIM = "#007a99"   # Cyan atténué (titres de section)
ORANGE   = "#ff6b1a"   # Couleur du bouton reset
GREEN    = "#00ff88"   # Couleur du bouton lancer
RED      = "#ff3333"   # Couleur d'alerte / arrêt
TEXT     = "#c8e8ff"   # Texte principal
TEXT2    = "#4a7a9b"   # Texte secondaire (labels)
TEXT3    = "#1a3a55"   # Texte tertiaire (peu utilisé)
MONO     = '"Consolas","Courier New",monospace'  # Police monospace


# ── Feuille de style globale de l'application ────────────────────────────────
APP_STYLE = f"""
QMainWindow, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: {MONO};
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    background: {BG};
    border: 2px solid {CYAN};
    margin: -6px 0;
}}
QSlider::handle:horizontal:hover {{
    background: {CYAN};
    border-color: #ffffff;
}}
QSlider::sub-page:horizontal {{
    background: {CYAN};
    border-radius: 3px;
    height: 6px;
}}
QSlider::add-page:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}
QPushButton {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER2};
    border-radius: 6px;
    padding: 10px 16px;
    font-family: {MONO};
    font-size: 13px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background: #0d2035;
    border: 1px solid {CYAN};
    color: {CYAN};
}}
QPushButton:pressed {{
    background: rgba(0,212,255,0.15);
    border-color: {CYAN};
    color: {CYAN};
}}
"""


class HLine(QFrame):
    """Séparateur horizontal fin utilisé entre les sections du panneau."""
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BORDER}; border: none;")


class SectionTitle(QLabel):
    """Label stylisé servant de titre de section (ex: 'OBSTACLES', 'PARAMÈTRES FLUIDE')."""
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            color: {CYAN_DIM};
            font-size: 10px;
            font-family: {MONO};
            letter-spacing: 3px;
            padding: 8px 0 4px 0;
        """)


class MainWindow(QMainWindow):
    """
    Fenêtre principale de la simulation de dynamique des fluides.

    Contient :
    - Un viewport 3D (Scene3D / PyVista) à gauche
    - Un panneau de contrôle à droite géré par un QStackedWidget :
        * Page 0 : contrôles généraux (run/reset, choix d'obstacle, paramètres fluide)
        * Page 1 : configuration d'une forme sélectionnée (dimensions + position XYZ)
    """

    def __init__(self):
        super().__init__()

        # ── État interne ──────────────────────────────────────────────────────
        self.pause = True                   # True = simulation arrêtée
        self.forme_selectionnee = None      # Nom de la forme en cours de configuration
        self.grille = Grille(5, 5, 10)      # Grille de simulation (5x5x10 cellules)
        self.police_scientifique = QFont("Consolas", 13)

        # ── Fenêtre ───────────────────────────────────────────────────────────
        self.resize(1280, 720)
        self.setWindowTitle("DYNAMIQUE DES FLUIDES SIM")
        self.setStyleSheet(APP_STYLE)

        # ── Widget central et layout principal (horizontal) ───────────────────
        self.centre = QWidget()
        self.setCentralWidget(self.centre)
        self.layout_principal = QHBoxLayout(self.centre)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        # ── Zone viewport 3D (côté gauche) ───────────────────────────────────
        self.scene_containerScene = QWidget()
        self.scene_containerScene.setStyleSheet(f"background:{BG};")
        self.scene_layoutScene3D = QVBoxLayout(self.scene_containerScene)
        self.scene_layoutScene3D.setContentsMargins(0, 0, 0, 0)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)
        self.layout_principal.addWidget(self.scene_containerScene)

        self.scene.forme.connect(self.recevoir_forme)

        # --- Stack pour panneau / édition ---
        # ── Pile de panneaux latéraux (côté droit) ───────────────────────────
        self.stack = QStackedWidget()
        self.forme_en_scene = None  # Référence à l'acteur temporaire affiché

        # ════════════════════════════════════════════════════════════════════
        # PAGE 0 — Panneau de contrôle principal
        # ════════════════════════════════════════════════════════════════════
        self.panneau = QWidget()
        self.panneau.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        self.layout_controles = QVBoxLayout(self.panneau)
        self.layout_controles.setContentsMargins(18, 16, 18, 16)
        self.layout_controles.setSpacing(25)

        # ── En-tête : titre + indicateur de statut ────────────────────────
        ligne_principale = QHBoxLayout()
        title_lbl = QLabel("FLUID SIM")
        title_lbl.setStyleSheet(f"""
            color: {CYAN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        self.status_dot = QLabel("◉ RUN")
        self.status_dot.setStyleSheet(f"""
            color: {TEXT2};
            font-size: 11px;
            letter-spacing: 2px;
        """)
        ligne_principale.addWidget(title_lbl)
        ligne_principale.addStretch()
        ligne_principale.addWidget(self.status_dot)
        self.layout_controles.addLayout(ligne_principale)
        self.layout_controles.addWidget(HLine())
        self.layout_controles.addSpacing(4)

        # ── Boutons RUN / RESET ───────────────────────────────────────────
        self.boutons = QHBoxLayout()
        self.boutons.setSpacing(8)

        self.boutonRun = QPushButton("▶  LANCER")
        self.boutonRun.setFixedHeight(46)
        self.boutonRun.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,255,136,0.08);
                color: {GREEN};
                border: 1px solid rgba(0,255,136,0.5);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
        """)

        self.bouton_reset = QPushButton("↺")
        self.bouton_reset.setFixedSize(46, 46)
        self.bouton_reset.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,26,0.08);
                color: {ORANGE};
                border: 1px solid rgba(255,107,26,0.4);
                border-radius: 6px;
                font-size: 18px;
            }}
            QPushButton:hover {{ background: rgba(255,107,26,0.18); border-color: {ORANGE}; }}
        """)

        self.boutons.addWidget(self.boutonRun)
        self.boutons.addWidget(self.bouton_reset)
        self.boutonRun.clicked.connect(self.animerRun)
        self.bouton_reset.clicked.connect(self.animerReset)
        self.layout_controles.addLayout(self.boutons)
        self.layout_controles.addSpacing(8)
        self.layout_controles.addWidget(HLine())

        # ── Grille de sélection des obstacles géométriques ────────────────
        self.layout_controles.addWidget(SectionTitle("OBSTACLES"))

        self.formesGeometriqueLigneDuHaut = QHBoxLayout()
        self.formesGeometriqueLigneDuHaut.setSpacing(6)
        self.formesGeometriqueLigneDuBas  = QHBoxLayout()
        self.formesGeometriqueLigneDuBas.setSpacing(6)

        # (image, identifiant_forme, couleur_unused, ligne_cible)
        formes_config = [
            ("realSphere.png", "sphere",   "red", self.formesGeometriqueLigneDuHaut),
            ("prisme.png",     "prisme",   "red", self.formesGeometriqueLigneDuHaut),
            ("cube.png",       "cube",     "red", self.formesGeometriqueLigneDuHaut),
            ("cylindre.png",   "cylindre", "red", self.formesGeometriqueLigneDuBas),
            ("Pyramide.png",   "pyramide", "red", self.formesGeometriqueLigneDuBas),
            ("fleche.png",     "fleche",   "red", self.formesGeometriqueLigneDuBas),
        ]

        # Création dynamique d'un bouton icône pour chaque forme
        for image, forme, couleur, ligne in formes_config:
            btn = QPushButton("")
            btn.setIcon(QPixmap(image))
            btn.setIconSize(QSize(60, 60))
            btn.setFixedSize(90, 90)
            btn.setToolTip(forme.upper())
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {SURFACE};
                    border: 1px solid {BORDER2};
                    border-radius: 10px;
                }}
                QPushButton:hover {{
                    background: rgba(0,212,255,0.12);
                    border: 1px solid {CYAN};
                }}
                QPushButton:pressed {{
                    background: rgba(0,212,255,0.25);
                    border: 2px solid {CYAN};
                }}
            """)
            # Capture de `forme` par défaut pour éviter la closure tardive
            btn.clicked.connect(lambda checked, f=forme: self.ouvrir_panneau_forme(f))
            ligne.addWidget(btn)

        self.layout_controles.addLayout(self.formesGeometriqueLigneDuHaut)
        self.layout_controles.addSpacing(6)
        self.layout_controles.addLayout(self.formesGeometriqueLigneDuBas)
        self.layout_controles.addSpacing(4)
        self.layout_controles.addWidget(HLine())

        # ── Sliders des paramètres physiques du fluide ────────────────────
        self.layout_controles.addWidget(SectionTitle("PARAMÈTRES FLUIDE"))

        self.texte_temperature, self.slider_temperature = self.creer_bloc("Température", 0, 30,    "°C")
        self.layout_controles.addSpacing(6)
        self.texte_viscous,     self.slider_viscous     = self.creer_bloc("Viscosité",   0, 1000,  "mPa")
        self.layout_controles.addSpacing(6)
        # facteur=10 pour obtenir une résolution décimale (ex: 101.4 kPa)
        self.texte_pression,    self.slider_pression    = self.creer_bloc("Pression",    0, 301.4, "kPa", 10)
        self.layout_controles.addSpacing(6)
        self.texte_vitesse,     self.slider_vitesse     = self.creer_bloc("Vitesse",     0, 100,   "m/s")
        self.layout_controles.addStretch()

        # ════════════════════════════════════════════════════════════════════
        # PAGE 1 — Panneau de configuration d'une forme
        # ════════════════════════════════════════════════════════════════════
        self.scene2_container = QWidget()
        self.scene2_container.setStyleSheet(f"background:{PANEL}; border-left: 1px solid {BORDER};")
        self.scene2_layout = QVBoxLayout(self.scene2_container)
        self.scene2_layout.setContentsMargins(18, 16, 18, 16)
        self.scene2_layout.setSpacing(50)

        # ── Bouton retour vers la page principale ─────────────────────────
        btn_back = QPushButton("← RETOUR")
        btn_back.setFixedHeight(38)
        btn_back.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(btn_back)
        self.scene2_layout.addWidget(HLine())

        # ── Nom de la forme sélectionnée ──────────────────────────────────
        self.label_forme_choisie = QLabel("FORME")
        self.label_forme_choisie.setFont(self.police_scientifique)
        self.label_forme_choisie.setStyleSheet(f"""
            color: {CYAN};
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 3px;
            padding: 6px 0 2px 0;
        """)
        self.scene2_layout.addWidget(self.label_forme_choisie)

        # ── Zone de sliders spécifiques à la forme (générée dynamiquement) ─
        self.layout_sliders_forme = QVBoxLayout()
        self.layout_sliders_forme.setSpacing(8)
        self.scene2_layout.addLayout(self.layout_sliders_forme)
        self.sliders_forme = {}
        self.labels_forme = {}

        # ── Sliders de position XYZ ───────────────────────────────────────
        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addWidget(SectionTitle("POSITION"))

        self.sliders_xyz = {}  # { 'x'|'y'|'z': QSlider }
        for axe, max_val in zip(["X", "Y", "Z"], [self.grille.x, self.grille.y, self.grille.z]):
            ligne = QHBoxLayout()
            ligne.setSpacing(10)

            axe_lbl = QLabel(axe)
            axe_lbl.setFixedWidth(16)
            axe_lbl.setStyleSheet(f"color:{CYAN}; font-size:25px; font-weight:bold;")

            # Valeur stockée en centièmes pour simuler un float (0.00 → max_val)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, int(max_val * 100))
            slider.setValue(0)

            label_axe = QLabel("0.00")
            label_axe.setFixedWidth(42)
            label_axe.setFont(self.police_scientifique)
            label_axe.setStyleSheet(f"color:{TEXT}; font-size:13px;")

            # Affiche la valeur décimale réelle (v / 100)
            slider.valueChanged.connect(lambda v, l=label_axe, a=axe.lower(): l.setText(f"{v/100:.2f}"))

            ligne.addWidget(axe_lbl)
            ligne.addWidget(slider)
            ligne.addWidget(label_axe)
            self.scene2_layout.addLayout(ligne)
            self.sliders_xyz[axe.lower()] = slider

        self.scene2_layout.addWidget(HLine())
        self.scene2_layout.addSpacing(6)

        # ── Bouton CONFIRMER ──────────────────────────────────────────────
        self.bouton_confirmer = QPushButton("✔  CONFIRMER")
        self.bouton_confirmer.setFixedHeight(44)
        self.bouton_confirmer.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,212,255,0.10);
                color: {CYAN};
                border: 1px solid rgba(0,212,255,0.5);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,212,255,0.22); }}
        """)
        self.bouton_confirmer.clicked.connect(self.confirmer_forme)
        self.scene2_layout.addWidget(self.bouton_confirmer)

        # ── Bouton SUPPRIMER ──────────────────────────────────────────────
        self.bouton_supprimer = QPushButton("✕  SUPPRIMER")
        self.bouton_supprimer.setFixedHeight(44)
        self.bouton_supprimer.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,51,51,0.08);
                color: {RED};
                border: 1px solid rgba(255,51,51,0.4);
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(255,51,51,0.20); }}
        """)
        self.bouton_supprimer.clicked.connect(self.supprimer_forme)
        self.scene2_layout.addWidget(self.bouton_supprimer)
        self.scene2_layout.addStretch()

        # ── Ajout des deux pages dans la pile et insertion dans le layout ─
        self.stack.addWidget(self.panneau)          # index 0
        self.stack.addWidget(self.scene2_container) # index 1
        self.layout_principal.addWidget(self.stack)

        # ── Définition des paramètres ajustables par forme ────────────────
        # Format : { nom_forme: [(nom_param, min, max), ...] }
        self.parametres_formes = {
            "sphere":   [("rayon", 1, 3)],
            "cube":     [("c", 1, 3)],
            "cylindre": [("rayon", 1, 3), ("h", 1, 3)],
            "prisme":   [("l", 1, 3), ("w", 1, 3), ("h", 1, 3)],
            "pyramide": [("h", 1, 3)],
            "fleche":   [("l", 1, 3), ("w", 1, 3)],
        }

        # ── Timer de la boucle de simulation (cible ~30 fps) ─────────────
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_simulation)

    def update_slider_position(self, v, l, a,):
        l.setText(f"{a}: {v / 100:.2f}")
        if self.forme_en_scene not in self.scene.pos_current:
            return

        pos = v/100
        x, y, z = self.scene.pos_current[self.forme_en_scene]
        if a == "x":
            self.scene.deplacement(pos,y, z)
        elif a == "y":
            self.scene.deplacement(x, pos, z)
        elif a == "z":
            self.scene.deplacement(x, y, pos)


    def generer_sliders_forme(self, nom_forme):
        self.sliders_forme.clear()
        # Suppression des anciens widgets du layout
        while self.layout_sliders_forme.count():
            item = self.layout_sliders_forme.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.sliders_forme.clear()
        self.labels_forme.clear()

        for param, min_val, max_val in self.parametres_formes.get(nom_forme, []):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setSpacing(10)

            param_lbl = QLabel(param.upper())
            param_lbl.setFixedWidth(52)
            param_lbl.setStyleSheet(f"color:{TEXT2}; font-size:12px; letter-spacing:1px;")

            # Valeur en centièmes pour la précision décimale
            slider = QSlider(Qt.Horizontal)
            slider.setRange(int(min_val * 100), int(max_val * 100))
            slider.setValue(int(min_val * 100))

            label = QLabel(f"{min_val:.2f}")
            label.setFixedWidth(42)
            label.setFont(self.police_scientifique)
            label.setStyleSheet(f"color:{TEXT}; font-size:13px;")

            slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v / 100:.2f}"))

            layout.addWidget(param_lbl)
            layout.addWidget(slider)
            layout.addWidget(label)

            self.layout_sliders_forme.addWidget(container)
            self.sliders_forme[param] = slider
            self.labels_forme[param] = label

    def creer_bloc(self, nom, min_val, max_val, unite="", facteur=1):
        """
        Crée un bloc label + slider pour un paramètre physique du fluide,
        l'ajoute au panneau principal et retourne (QLabel_nom, QSlider).

        Args:
            nom      : Nom du paramètre (affiché en majuscules).
            min_val  : Valeur minimale réelle du paramètre.
            max_val  : Valeur maximale réelle du paramètre.
            unite    : Unité affichée à côté de la valeur (ex: '°C').
            facteur  : Multiplicateur interne du slider (utile pour les décimales).
        """
        bloc = QVBoxLayout()
        bloc.setSpacing(6)

        ligne = QHBoxLayout()
        texte = QLabel(nom.upper())
        texte.setStyleSheet(f"color:{TEXT2}; font-size:12px; letter-spacing:1px;")
        label_valeur = QLabel(f"{min_val} {unite}")
        label_valeur.setFont(self.police_scientifique)
        label_valeur.setStyleSheet(f"color:{CYAN}; font-size:14px; font-weight:bold;")
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

    def _connecter_sliders_forme(self):
        for param, slider in self.sliders_forme.items():
            try:
                slider.valueChanged.disconnect()
            except TypeError:
                pass
            label = self.labels_forme[param]
            slider.valueChanged.connect(lambda v, l=label: l.setText(f"{v / 100:.2f}"))
            slider.valueChanged.connect(self.mettre_a_jour_dimensions)



    def ouvrir_panneau_forme(self, nom_forme):
        """
        Bascule vers la page 1 (configuration de forme) :
        - Met à jour le titre et réinitialise les sliders XYZ.
        - Génère les sliders propres à la forme sélectionnée.
        - Crée une forme temporaire dans la scène 3D.
        - Connecte chaque slider de dimension à mettre_a_jour_dimensions.
        """
        self.forme_selectionnee = nom_forme
        self.label_forme_choisie.setText(nom_forme.upper())

        # Réinitialisation de la position à l'origine
        for slider in self.sliders_xyz.values():
            slider.setValue(0)

        self.generer_sliders_forme(nom_forme)

        # Valeurs par défaut = minima de chaque paramètre
        default_valeurs = {param: min_val for param, min_val, max_val in self.parametres_formes.get(nom_forme, [])}
        self.forme_en_scene = self.scene.add_forme(nom_forme, default_valeurs)
        self.scene.acteur_current = self.forme_en_scene


        self._connecter_sliders_forme()

        self.stack.setCurrentIndex(1)

    def confirmer_forme(self):
        """Revient à la page principale (index 0) sans supprimer la forme."""
        self.stack.setCurrentIndex(0)

    def supprimer_forme(self):
        """
        Supprime l'acteur 3D temporaire de la scène et revient au panneau principal.
        """
        print("in")
        if self.forme_en_scene is not None:
            print("out")
            self.scene.supprimer(self.scene.acteur_current)
        self.stack.setCurrentIndex(0)

    def mettre_a_jour_dimensions(self):
        """
        Appelée à chaque changement d'un slider de dimension de forme.
        Lit toutes les valeurs courantes et les transmet à la scène 3D.
        """
        if self.forme_en_scene is None:
            return
        valeurs = {nom: slider.value() / 100 for nom, slider in self.sliders_forme.items()}
        self.scene.acteur_current = self.forme_en_scene
        self.scene.changer_dimensions_dict(valeurs)

    def update_value(self, label, value, unite, facteur):
        """
        Met à jour le label d'affichage d'un paramètre fluide.
        Affiche un flottant si facteur > 1, sinon un entier.
        """
        valeur_reelle = value / facteur
        if facteur > 1:
            label.setText(f"{valeur_reelle:.2f} {unite}")
        else:
            label.setText(f"{int(valeur_reelle)} {unite}")

    def update_simulation(self):
        """
        Slot appelé à chaque tick du timer (~30 fps).
        Avance la simulation d'un pas et rafraîchit la scène 3D.
        """
        self.grille.update_valeurs()
        self.scene.grille_3D.update_scene()

    def animerRun(self):
        """
        Bascule entre l'état RUNNING et IDLE :
        - IDLE → RUNNING : démarre le timer, met à jour le bouton en rouge.
        - RUNNING → IDLE : arrête le timer, remet le bouton en vert.
        """
        if not self.pause:
            # ── Passage à IDLE ────────────────────────────────────────────
            self.boutonRun.setText("▶  LANCER")
            self.boutonRun.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0,255,136,0.08);
                    color: {GREEN};
                    border: 1px solid rgba(0,255,136,0.5);
                    border-radius: 6px;
                    font-size: 14px; font-weight: bold; letter-spacing: 2px;
                }}
                QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
            """)
            self.status_dot.setText("◉ IDLE")
            self.status_dot.setStyleSheet(f"color:{TEXT2}; font-size:11px; letter-spacing:2px;")
            self.timer.stop()
        else:
            # ── Passage à RUNNING ─────────────────────────────────────────
            self.boutonRun.setText("■  ARRÊTER")
            self.boutonRun.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,51,51,0.10);
                    color: {RED};
                    border: 1px solid rgba(255,51,51,0.5);
                    border-radius: 6px;
                    font-size: 14px; font-weight: bold; letter-spacing: 2px;
                }}
                QPushButton:hover {{ background: rgba(255,51,51,0.22); border-color: {RED}; }}
            """)
            self.status_dot.setText("◉ RUN")
            self.status_dot.setStyleSheet(f"color:{GREEN}; font-size:11px; letter-spacing:2px;")
            self.timer.start(1000 // 30)  # ~30 fps
        self.pause = not self.pause

    def animerReset(self):
        """
        Réinitialise complètement la simulation :
        - Arrête le timer et passe en état IDLE.
        - Détruit et recrée la scène 3D et la grille.
        - Remet tous les sliders de paramètres fluide à zéro.
        """
        self.timer.stop()
        self.pause = True
        self.boutonRun.setText("▶  LANCER")
        self.boutonRun.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,255,136,0.08);
                color: {GREEN};
                border: 1px solid rgba(0,255,136,0.5);
                border-radius: 6px;
                font-size: 14px; font-weight: bold; letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,255,136,0.18); border-color: {GREEN}; }}
        """)
        self.status_dot.setText("◉ IDLE")
        self.status_dot.setStyleSheet(f"color:{TEXT2}; font-size:11px; letter-spacing:2px;")

        # ── Remplacement de la scène PyVista ──────────────────────────────
        self.scene.plotter.close()
        self.scene_layoutScene3D.removeWidget(self.scene.plotter)
        self.scene.plotter.deleteLater()

        self.grille = Grille(5, 5, 10)
        self.scene = Scene3D(self.scene_containerScene, self.grille)
        self.scene_layoutScene3D.addWidget(self.scene.plotter)

        # ── Remise à zéro des paramètres fluide ───────────────────────────
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
        self._connecter_sliders_forme()

        for nom, slider in self.sliders_forme.items():
            valeur = params["params"].get(nom, 1)
            slider.blockSignals(True)
            slider.setValue(int(valeur * 100))
            slider.blockSignals(False)
            self.labels_forme[nom].setText(f"{valeur:.2f}")

        if acteur in self.scene.pos_current:
            x, y, z = self.scene.pos_current[acteur]
            self.sliders_xyz["x"].setValue(int(x * 100))
            self.sliders_xyz["y"].setValue(int(y * 100))
            self.sliders_xyz["z"].setValue(int(z * 100))

        self.stack.setCurrentIndex(1)