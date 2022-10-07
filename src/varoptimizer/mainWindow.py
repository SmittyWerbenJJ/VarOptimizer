from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
import signal

# The fondamental for working with python

from .Widgets import ui_mainWindow
from .eventHook import EventHook
from .optimizer import OptimizerArgs


class MainWindow(QMainWindow):
    setResizeResolution = QtCore.pyqtSignal(int)
    setImageResizeBool = QtCore.pyqtSignal(bool)
    onOpenFolderDialogClicked = QtCore.pyqtSignal()
    onInputDirTextChanged = QtCore.pyqtSignal(str)
    onResizeImageToggled = QtCore.pyqtSignal(int)
    onResizeImageResChanged = QtCore.pyqtSignal(int)
    onOptimizeButtonClicked = QtCore.pyqtSignal()
    onRestoreBackupToggled = QtCore.pyqtSignal(bool)
    onRecursiveToggled = QtCore.pyqtSignal(int)

    def __init__(self,iconPath=None, parent=None):
        # Qt signal when asynchronous processing is interrupted

        # Create settings for the software
        QMainWindow.__init__(self, parent)
        self.settings = QSettings("SmittyWerbenJJ", "VarOptimizer")
        self.settings.setFallbacksEnabled(False)
        self.version = "0.0.1"

        self.ui = ui_mainWindow.Ui_MainWindow()
        self.ui.setupUi(self)

        self.constructUI()
        self.ConnectSlots()

        # When the software are closed on console the software are closed
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if iconPath is not None:
            self.setWindowIcon(QtGui.QIcon(iconPath))


    def constructUI(self):

        # Set the MainWindow Title
        self.setWindowTitle("VarOptimizer - " + self.version)

        # hook up input folder text box
        self.ui.input_folder.textChanged.connect(
            self.onInputDirTextChanged.emit)

        self.ui.btn_SelectFolder.clicked.connect(
            self.onOpenFolderDialogClicked.emit)

        # hook up resize image toggle
        self.ui.chk_resizeImg.stateChanged.connect(
            self.onResizeImageToggled.emit)

        # hook up recursive Checkbox
        self.ui.chk_recursive.stateChanged.connect(
            self.onRecursiveToggled.emit)

        # hook up resize image combo box
        self.ui.cmb_resizeImg.currentIndexChanged.connect(
            self.onResizeResolutionChanged)

        # hook up optimize button
        self.ui.btn_Optimize.clicked.connect(self.onOptimizeButtonClicked.emit)

        # hook up the restore backups checkBox
        self.ui.chk_restoreBackups.stateChanged.connect(
            self.onRestoreBackupsToggled)

    def onResizeResolutionChanged(self):
        self.onResizeImageResChanged.emit(
            int(self.ui.cmb_resizeImg.currentText()))

    def onRestoreBackupsToggled(self):
        checked =self.ui.chk_restoreBackups.isChecked()
        self.onRestoreBackupToggled.emit(checked)

    def ConnectSlots(self):
        self.setResizeResolution.connect(self.setResizeResolution_DONTCALL)
        self.setImageResizeBool.connect(self.setImageResizeBool_DONTCALL)

    def setImageResizeBool_DONTCALL(self, value: bool):
        self.ui.chk_restoreBackups.setChecked(value)

    def setResizeResolution_DONTCALL(self, value: int):
        QComboBoxName = self.ui.cmb_resizeImg
        # get index with value
        AllItems = {
            QComboBoxName.itemText(i): i - 1 for i in range(QComboBoxName.count())
        }
        # set index to index with value
        self.ui.cmb_resizeImg.setCurrentIndex(AllItems[value])

    def getImageResizeCheckState(self):
        return self.ui.chk_resizeImg.isChecked()

    def getRestoreBackupsCheckState(self):
        return self.ui.chk_restoreBackups.isChecked()

    def getAllCurrentValues(self):
        ui = self.ui
        args = OptimizerArgs()
        args.dir = Path(ui.input_folder.text())
        args.optimizerOptions.resize = (
            True if ui.chk_resizeImg.checkState == Qt.Checked else False
        )
        args.optimizerOptions.resizeDimensions = int(
            ui.cmb_resizeImg.currentText())
        args.restoreBackupVars = self.getRestoreBackupsCheckState()
        
        return args

    def setInputFolderText(self, txt):
        self.ui.input_folder.setText(txt)
