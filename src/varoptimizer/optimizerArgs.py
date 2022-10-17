from pathlib import Path

from . import utils

# from .mainWindow import MainWindow
# from .progressDialog import ProgressDialog


class OptimizerArgs:
    def __init__(self) -> None:

        self.progressDialog: "ProgressDialog" = None
        self.mainMenuDialog: "MainWindow" = None
        self.recursive = False
        self.dir: Path
        self.restoreBackupVars: bool
        # self.optimizerOptions: utils.ImgConvertOption
        self.dir: Path = None
        self.restoreBackupVars: bool = True
        self.optimizerOptions = utils.ImgConvertOption()
