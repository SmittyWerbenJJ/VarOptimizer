from .commonImports import *
from .optimizer import Optimizer
from .pyqtimports import *


class ThreadWorker(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()
    kill = pyqtSignal()

    def __init__(self, parent=None) -> None:

        super().__init__(parent)
        self.optimizerArgs = None
        self.opt: Optimizer
        self.finished.connect(self.quit)

    def run(self):
        self.opt = Optimizer()
        self.kill.connect(self.opt.killAllProcesses)
        """Long-running task."""
        if self.optimizerArgs is None:
            self.finished.emit()
            return
        self.opt.startOptimisation(self.optimizerArgs)
        self.finished.emit()

    def quit(self):
        self.kill.emit()
