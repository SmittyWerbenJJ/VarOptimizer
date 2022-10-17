import multiprocessing
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .Widgets import *


def main():
    import varoptimizer.uiController as uiController

    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    controller = uiController.UiController()
    controller.showMainWindow()

    sys.exit(app.exec())
