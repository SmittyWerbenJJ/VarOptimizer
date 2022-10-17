from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .eventHook import EventHook
from .Widgets import ui_ProgressDialog


class ProgressDialog(QDialog):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """

    onUpdateTaskProgress_DONTCALL = EventHook()
    onResizeImageToggled = EventHook()

    # total progress
    setTotalProgressRangeMax = QtCore.pyqtSignal(int)
    setTotalProgress = QtCore.pyqtSignal(int)
    resetTotalProgress = QtCore.pyqtSignal()
    updateTotalProgress = QtCore.pyqtSignal(int)
    setTotalProgressDescription = QtCore.pyqtSignal(str)

    # tasj progress
    setTaskProgressRangeMax = QtCore.pyqtSignal(int)
    setTaskProgress = QtCore.pyqtSignal(int)
    resetTaskProgress = QtCore.pyqtSignal()
    updateTaskProgress = QtCore.pyqtSignal(int)
    setTaskProgresssDescription = QtCore.pyqtSignal(str)

    # misc
    resetAllProgressbars = QtCore.pyqtSignal()
    writeTextLine = QtCore.pyqtSignal(str)
    clearTextBox = QtCore.pyqtSignal()
    onCancel = QtCore.pyqtSignal()

    def __init__(self, iconPath=None, parent=None):
        super().__init__(parent)
        self.ui = ui_ProgressDialog.Ui_DialogProgress()
        self.ui.setupUi(self)
        self.ConnectSlots()
        self.initUI()

        self.totalProgress = 0
        self.taskProgress = 0
        self.log = []

        if iconPath is not None:
            self.setWindowIcon(QtGui.QIcon(iconPath))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.onCancel.emit()
        return super().closeEvent(a0)

    def initController(self, controller):
        self.controller = controller
        self.controller.startOptimizing()

    def initUI(self):
        # Set the MainWindow Title

        self.setWindowTitle("Optimizing ...")
        self.setTaskProgressRangeMax.emit(100)
        self.setTotalProgressRangeMax.emit(100)
        self.resetAllProgressbars_DONTCALL()
        self.ui.textbox.setText("")

    def ConnectSlots(self):

        self.setTotalProgressRangeMax.connect(self.setTotalRangeMax_DONTCALL)
        self.setTotalProgress.connect(self.setTotalProgress_DONTCALL)
        self.resetTotalProgress.connect(self.resetTotalProgress_DONTCALL)
        self.updateTotalProgress.connect(self.updateTotalProgress_DONTCALL)
        self.setTotalProgressDescription.connect(self.setTotalDescription_DONTCALL)

        self.setTaskProgressRangeMax.connect(self.setTaskRangeMax_DONTCALL)
        self.setTaskProgress.connect(self.setTaskProgress_DONTCALL)
        self.resetTaskProgress.connect(self.resetTaskProgress_DONTCALL)
        self.updateTaskProgress.connect(self.updateTaskProgress_DONTCALL)
        self.setTaskProgresssDescription.connect(self.setTaskDescription_DONTCALL)

        self.writeTextLine.connect(self.postError_DONTCALL)
        self.clearTextBox.connect(self.clearTextBox_DONTCALL)
        self.resetAllProgressbars.connect(self.resetAllProgressbars_DONTCALL)

    def resetEverything(self):
        self.resetAllProgressbars_DONTCALL()
        self.clearTextBox_DONTCALL()

    def setTotalRangeMax_DONTCALL(self, max):
        self.ui.progressBar_totalprogress.setRange(0, max)
        self.updateUI()

    def setTotalProgress_DONTCALL(self, value):
        self.ui.progressBar_totalprogress.setValue(value)

    def resetTotalProgress_DONTCALL(
        self,
    ):
        self.ui.progressBar_totalprogress.setValue(0)

    def updateTotalProgress_DONTCALL(self, updateValue):
        currentProgress = self.ui.progressBar_totalprogress.value()
        self.ui.progressBar_totalprogress.setValue(currentProgress + updateValue)
        self.updateUI()

    def setTotalDescription_DONTCALL(self, desc):
        self.ui.label_totalprogress.setText(str(desc))
        self.updateUI()

    def setTaskRangeMax_DONTCALL(self, max):
        self.ui.progressBar_taskProgress.setRange(0, max)
        self.updateUI()

    def setTaskProgress_DONTCALL(self, value):
        self.ui.progressBar_taskProgress.setValue(value)

    def resetTaskProgress_DONTCALL(
        self,
    ):
        self.ui.progressBar_taskProgress.setValue(0)

    def updateTaskProgress_DONTCALL(self, updateValue):
        currentProgress = self.ui.progressBar_taskProgress.value()
        self.ui.progressBar_taskProgress.setValue(currentProgress + updateValue)
        self.updateUI()

    def setTaskDescription_DONTCALL(self, desc):
        self.ui.label_taskprogress.setText(str(desc))
        self.updateUI()

    def resetAllProgressbars_DONTCALL(self):
        self.setTotalProgressRangeMax.emit(100)
        self.setTaskProgressRangeMax.emit(100)
        self.setTotalProgressDescription.emit("Total Progress ...")
        self.setTaskProgresssDescription.emit("...")
        self.resetTotalProgress.emit()
        self.resetTaskProgress.emit()
        self.updateUI()

    def clearTextBox_DONTCALL(self):
        self.ui.textbox.clear()

    def postError_DONTCALL(self, text):
        self.ui.textbox.append(text + "\n")

    def updateUI(self):
        QApplication.processEvents()
