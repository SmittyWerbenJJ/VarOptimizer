import os
import queue
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from eventHook import EventHook
from mainWindow import MainWindow
from optimizer import Optimizer
from progressDialog import ProgressDialog
from vamOptimizerUtils import *
from Widgets import *
from Widgets import Ui_MainWindow


class ThreadWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    kill = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.optimizerArgs = None
        self.opt = Optimizer()
        self.kill.connect(self.opt.killAllProcesses)
        self.finished.connect(self.quit)

    def run(self):
        """Long-running task."""
        if self.optimizerArgs is None:
            self.finished.emit()
            return
        self.opt.optimizeFolder(self.optimizerArgs)
        self.finished.emit()

    def quit(self):
        self.kill.emit()


class UiController(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    backGroundThread: QThread
    backgroundworker = ThreadWorker()

    def __init__(self, ):
        super(UiController, self).__init__()
        self.cwd = str(Path(__file__).parent)
        self.workQueue = queue.Queue()
        self.onProgressUpdate = EventHook()
        self.optimizerArgs = OptimizerArgs()

        self.mainWindow = MainWindow()
        self.progressWindow = ProgressDialog()

        self.initMainWindow()
        self.initProgressWindow()
        self.optimizerArgs.progressDialog = self.progressWindow
        self.optimizerArgs.mainMenuDialog = self.mainWindow

    def initMainWindow(self):
        ui = self.mainWindow.ui

        # hook up ui events from main menu objects
        self.mainWindow.onOpenFolderDialogClicked.connect(
            self.userSelectNewInputDir)
        self.mainWindow.onOptimizeButtonClicked .connect(
            self.showProgressWindow)
        self.mainWindow.onRestoreBackupToggled .connect(
            self.userToggleRestoreBackup)
        self.mainWindow.onInputDirTextChanged .connect(self.setNewFolderPath)
        self.mainWindow.onResizeImageResChanged .connect(
            self.setResizeImageResolution)
        self.mainWindow.onResizeImageToggled .connect(
            self.setResizeImageEnabled)
        self.mainWindow.onRecursiveToggled.connect(self.setRecursive)

        self.setResizeImageResolution(ui.cmb_resizeImg.currentText())
        self.setResizeImageEnabled(ui.chk_resizeImg.isChecked())
        self.setNewFolderPath(os.getcwd(), setInUI=True)
        self.setRecursive(ui.chk_recursive.isChecked())

        self.optimizerArgs = self.mainWindow.getAllCurrentValues()

    def initProgressWindow(self):
        ui = self.progressWindow.ui
        self.progressWindow.onCancel.connect(self.cancelOptimisation)

    def showMainWindow(self):
        self.mainWindow.show()

    def showProgressWindow(self):
        self.progressWindow.resetAllProgressbars.emit()
        self.progressWindow.clearTextBox.emit()
        if not self.progressWindow.isVisible():
            self.progressWindow.show()

        self.startOptimizing()

    def startOptimizing(self):
        # if self.backgroundworker is None:
        self.backgroundworker = ThreadWorker()
        # self.progressWindow.onCancel.connect(self.backgroundworker.kill.emit)

        # if self.backGroundThread is None:

        self.backGroundThread = QThread()
        self.backGroundThread.setObjectName(
            "Optimizer Manager BackgroundThread")
        self.backgroundworker.optimizerArgs = self.optimizerArgs
        self.backgroundworker.moveToThread(self.backGroundThread)

        self.backGroundThread.started.connect(self.backgroundworker.run)
        self.backgroundworker.finished.connect(self.backGroundThread.quit)
        # self.backgroundworker.finished.connect(
        #     self.backgroundworker.deleteLater)
        # self.backGroundThread.finished.connect(
        #     self.backGroundThread.deleteLater)

        self.backGroundThread.start()

    def userToggleRestoreBackup(self, status):
        self.optimizerArgs.restoreBackupVars = status

    def userSelectNewInputDir(self):
        self.showOpenFolderDialog(assignDir=True)
        self.mainWindow.setInputFolderText(str(self.optimizerArgs.dir))

    def showOpenFolderDialog(self, assignDir=False):
        options = QFileDialog.Option.ShowDirsOnly  # | QFileDialog.DontResolveSymlinks

        directory = QFileDialog.getExistingDirectory(
            parent=self.mainWindow,
            caption="Select Folder with .var files",
            directory=self.cwd,
            options=options,
        )

        if directory and assignDir:
            self.setNewFolderPath(directory, setInUI=True)

        return directory

    def setNewFolderPath(self, newPath, setInUI=False):
        if newPath != "":
            path = Path(newPath)
            if path.exists():
                self.optimizerArgs.dir = path
        if setInUI:
            self.mainWindow.ui.input_folder.setText(
                str(self.optimizerArgs.dir))

    def setResizeImageEnabled(self, activeState):
        if type(activeState) == int:
            doResize = False if activeState == 0 else True
            self.optimizerArgs.optimizerOptions.resize = doResize

    def setResizeImageResolution(self, newResolution):
        newRes = int(newResolution)
        self.optimizerArgs.optimizerOptions.resizeDimensions = newRes

    def setRecursive(self, doRecursive):
        doRecursive = False if doRecursive == 0 else True
        self.optimizerArgs.recursive = doRecursive

    def cancelOptimisation(self):
        if self.backgroundworker is None:
            return
        self.backgroundworker.kill.emit()
