import pyvista as pv
from pyvista import QtInteractor


class Scene3D:
    def __init__(self, parent):
        self.plotter = QtInteractor(parent)
