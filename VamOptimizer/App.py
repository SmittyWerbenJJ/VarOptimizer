
import argparse
import sys
import time
import asyncio
import multiprocessing
from PyQt5.QtCore import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


from uiController import UiController
from Widgets import *
from progressDialog import ProgressDialog
from mainWindow import MainWindow


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dir",
        help="The Directory to scan"
    )
    parser.add_argument(
        "-r",
        help="Recursive Scan: Scall all subfolders",
        action="store_true",
    )
    parser.add_argument(
        "--resize",
        help="resizes the images: This number will be the max width/height of the image and preserves the Aspect Ratio",
        type=int
    )
    args = parser.parse_args()
    return args


def main():
    # MainWindow_ = MainWindow()
    app = QApplication(sys.argv)
    controller = UiController()
    controller.showMainWindow()

    sys.exit(app.exec())


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
