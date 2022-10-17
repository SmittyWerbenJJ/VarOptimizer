"""
Tool optimize textures within var files

this tool scans var files and converts all png files (with unused alpha ) to jpeg files with 100% quality

automation steps:
scan dir for var files
open each var file

---loop
get var file size on disk
scan var file for png files
create temp dir
move non-png files to temp dir

-load png file in ram and convert to jpeg
-place converted jpeg file in temp dir  with same zip folder structure

zip temp dir fast
rename old temp dir: add suffix .backupPNG
move zipped temp dir to old var path
---

get var file size on disk
show size difference

"""

import pickle
import shutil
import zipfile

# from varoptimizer import archiveInfo
from io import *
from multiprocessing.pool import AsyncResult, Pool, ThreadPool
from queue import Queue
from traceback import format_exc

from pyparsing import Opt

from varoptimizer import archiveInfo

from . import utils
from .archiveInfo import ArchiveInfo
from .commonImports import *
from .optimizerArgs import OptimizerArgs
from .progressDialog import ProgressDialog


class Optimizer:
    instance = None

    def __init__(self) -> None:
        # multiprocessing stuff
        self.manager = multiprocessing.Manager()

        self.errorQueue: Queue
        self.encounteredErrors: int
        self.progressdialog: ProgressDialog
        self.optimizer_args: OptimizerArgs
        Optimizer.instance = self

    def initOptimizer(self, args: "OptimizerArgs"):
        # self.errorQueue = multiprocessing.Queue()
        self.errorQueue = self.manager.Queue()
        self.encounteredErrors = 0
        self.optimizer_args = args
        self.progressdialog = args.progressDialog

        # initAllCPUS
        self.CPUCores = max(1, os.cpu_count() - 1)
        self.processPool = Pool(self.CPUCores)
        # self.processPool = ThreadPool(self.CPUCores)

    def startOptimisation(self, args: OptimizerArgs):
        try:
            """
            process: we scan the folder for var files (and backups) and check if they are valid zipfiles
            then we iterate over those var files and execute the chain of commands to optimize those files.
            the optimisation will take place with all cpu cores. after each run we increase the total counter.
            within each run we increase a sub-counter
            """
            self.initOptimizer(args)
            self.optimizeFolder(args)
        except Exception as e:
            Optimizer.postError("Error While Optimizing:\n" + traceback.format_exc())

    def optimizeFolder(self, args: OptimizerArgs):
        # init vars
        self.optimizer_args = args
        self.progressdialog = self.optimizer_args.progressDialog
        self.chunksize = max(1, 1)  # int(len(varFiles)/CPUCores))

        # init ui
        self.initProgressBarOnStartup(self.progressdialog)

        # get all var files
        varFiles: list[Path] = utils.get_all_files_in_dir_by_extension(
            self.optimizer_args.dir, ".var", recursive=self.optimizer_args.recursive
        )

        # restore backups
        if self.optimizer_args.restoreBackupVars:
            backups = []
            for folderwithbackups in [x.parent for x in varFiles]:
                bb = self.findBackupVarFiles(folderwithbackups)
                if len(bb) >= 1:
                    backups.extend(bb)
            backups1 = list(set(backups))
            self.restoreBackupVars(backups1)

        # # validate var files
        # varFiles = vamOptimizerUtils.validateVarFiles(varFiles)

        # resetProgressBars
        self.progressdialog.setTotalProgressRangeMax.emit(len(varFiles))
        self.progressdialog.setTaskProgressRangeMax.emit(10)
        self.progressdialog.setTotalProgress.emit(0)
        self.progressdialog.setTotalProgressDescription.emit(
            "Optimizing " + str(len(varFiles)) + " .Var Files ... "
        )
        # self.progressdialog.setTaskProgressRangeMax.emit(len(varFiles))

        # asyncTasks = []
        # for vF in varFiles:
        #     asyncTask = None
        #     asyncArgs = utils.ArgsDict(
        #         varfile=vF,
        #         dir=self.optimizer_args.dir,
        #         restoreBackups=self.optimizer_args.restoreBackupVars,
        #         options=vars(self.optimizer_args.optimizerOptions),
        #         errorQueue=self.errorQueue,
        #         processPool=self.processPool,
        #     )
        #     asyncTask = self.processPool.starmap_async(
        #         Optimizer.optimizeVarFile,
        #         [(asyncArgs,)],
        #         callback=self.optimizerSuccessCallback,
        #         error_callback=self.optimizerErrorCallback,
        #     )
        #     asyncTasks.append(asyncTask)

        # init optimisation tasks
        # optimize
        # pendingTasks = len(asyncTasks)
        # while pendingTasks > 0:
        #     for task in asyncTasks:
        #         try:
        #             if task.get(timeout=1):
        #                 # self.updateTotalProgressbyOne()
        #                 pendingTasks -= 1
        #         except Exception as e:
        #             continue

        #         self.printErrorsFromQueue()
        #         # self.updateTaskbyOne()

        # allvarfiles=[]

        self.setUiNewTaskStatus(5, "...")
        for i, varfile in enumerate(varFiles):
            self.setUiNewTaskStatus(4, str(varfile.name) + " ...")
            archiveinfo = ArchiveInfo(varfile, imageConvertOption=args.optimizerOptions)

            utils.MP_ExtractConvertArchivedMetaFiles(
                self.processPool, archiveinfo, self.errorQueue
            )

            self.updateTaskbyOne()
            utils.MP_ExtractOtherFilesMP(self.processPool, archiveinfo, self.errorQueue)

            self.updateTaskbyOne()
            utils.MP_ExtractConvertImages(
                self.processPool, archiveinfo, args.optimizerOptions, self.errorQueue
            )

            self.updateTaskbyOne()
            utils.create_archive_for_ArchiveInfo(archiveinfo)

            self.updateTaskbyOne()
            utils.backupVarFile(archiveinfo)
            utils.finalizeTempVar(archiveinfo)

            if i + 1 == len(varFiles):
                shutil.rmtree(archiveinfo.tempDir, ignore_errors=True)
            self.updateTaskbyOne()
            self.updateTotalProgressbyOne()

        # all tasks finished
        self.progressdialog.setTaskProgresssDescription.emit("Done ...")
        self.progressdialog.setTotalProgressDescription.emit("Done ...")

        self.progressdialog.writeTextLine.emit(
            "Finished with " + str(self.encounteredErrors) + " Errors"
        )

    def setupTask2(self, archiveInfos: list[ArchiveInfo]) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            files = [x.filename for x in archInf.metaFiles]
            args = [(archInf.archivePath, files, archInf.tempDir, self.errorQueue)]
            asyncTask = self.processPool.starmap_async(
                utils.ExtractConvertArchivedImage, args
            )
            res.append(asyncTask)
        self.setUiNewTaskStatus(
            utils.utils.calcProgressBarMaxInt(res), "extracting-Convert MetaData..."
        )

        return res

    def setupTask3(self, archiveInfos: list[ArchiveInfo]) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            task3jpgFiles = [x.filename for x in archInf.jpgFiles]
            task3argsJPEG = [
                (archInf.archivePath, task3jpgFiles, archInf.tempDir, self.errorQueue)
            ]

            task3allOtherFiles = [x.filename for x in archInf.allOtherFiles]
            task3argsOther = [
                (
                    archInf.archivePath,
                    task3allOtherFiles,
                    archInf.tempDir,
                    self.errorQueue,
                )
            ]

            res.append(
                self.processPool.starmap_async(utils.extractFromArchive, task3argsJPEG)
            )

            res.append(
                self.processPool.starmap_async(utils.extractFromArchive, task3argsOther)
            )

        self.setUiNewTaskStatus(
            utils.utils.calcProgressBarMaxInt(res), "extracting JPG & other Files ..."
        )

        return res

    def setupTask4(
        self, archiveInfos: list[ArchiveInfo], args: OptimizerArgs
    ) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            for img in archInf.imgFiles:
                task4args = [
                    (
                        archInf.archivePath,
                        img.filename,
                        archInf.tempDir,
                        args.optimizerOptions,
                        self.errorQueue,
                    )
                ]
                res.append(
                    self.processPool.starmap_async(
                        utils.ExtractConvertArchivedImage, task4args
                    )
                )

        self.setUiNewTaskStatus(
            utils.calcProgressBarMaxInt(res), "Converting Images ..."
        )

        return res

    def setupTask5(self, archiveInfos: list[ArchiveInfo], chunksize: int):
        res = []
        for archInf in archiveInfos:
            task5args = [(archInf.tempDir, archInf.createdTempArchive)]
            res.append(
                self.processPool.starmap_async(
                    utils.create_archive, task5args, chunksize=chunksize
                )
            )

        self.setUiNewTaskStatus(
            utils.calcProgressBarMaxInt(res), "zipping Archives ..."
        )

        return res

    def setupTask6(
        self, archiveInfos: list[ArchiveInfo], chunksize: int, restoreBackups: bool
    ):
        res = []
        for archInf in archiveInfos:
            if restoreBackups is True:
                res.append(
                    self.processPool.starmap_async(
                        self.backupVarFile,
                        [(archInf.archivePath, self.errorQueue)],
                        chunksize=chunksize,
                    )
                )
            else:
                res.append(
                    self.processPool.starmap_async(
                        self.replaceVarFileWithTempVar,
                        [(archInf.archivePath, self.errorQueue)],
                        chunksize=chunksize,
                    )
                )
        if restoreBackups is True:
            self.setUiNewTaskStatus(
                utils.calcProgressBarMaxInt(res), "Backung Up Original Vars  ..."
            )
        else:
            self.setUiNewTaskStatus(
                utils.calcProgressBarMaxInt(res), "Replacing Var Files ..."
            )
        return res

    def initProgressBarOnStartup(self, progressdialog: ProgressDialog):
        progressdialog.resetAllProgressbars.emit()
        progressdialog.setTotalProgressRangeMax.emit(1)
        progressdialog.setTotalProgressDescription.emit("Loading ...")
        progressdialog.setTaskProgresssDescription.emit("Loading ...")

    def postError(error: str):
        instance = Optimizer.instance
        instance.progressdialog.writeTextLine.emit(error)

    def printErrorsFromQueue(self):
        try:
            error = self.errorQueue.get_nowait()
            if error is not None:
                self.progressdialog.writeTextLine.emit(error)
        except Exception as e:
            pass

    def updateTaskbyOne(self):
        self.progressdialog.updateTaskProgress.emit(1)
        self.printErrorsFromQueue()

    def updateTotalProgressbyOne(self):
        self.progressdialog.updateTotalProgress.emit(1)
        self.printErrorsFromQueue()

    def setUiNewTaskStatus(self, maxProgressNumber: int, taskDescription: str):
        self.progressdialog.setTaskProgressRangeMax.emit(maxProgressNumber)
        self.progressdialog.resetTaskProgress.emit()
        self.progressdialog.setTaskProgresssDescription.emit(taskDescription)
        time.sleep(0.001)

    def findBackupVarFiles(self, inputdir):
        backupfiles = utils.get_all_files_in_dir_by_extension(
            inputdir, ArchiveInfo.VARBACKUPSUFFIX
        )
        return backupfiles

    def restoreBackupVars(self, varBackups: list[Path]):
        for vBackup in varBackups:
            if vBackup.with_suffix("").exists():
                os.remove(vBackup.with_suffix(""))
            vBackup.rename(vBackup.with_suffix(""))

    def backupVarFile(self, varfile: Path, errorQueue: multiprocessing.Queue):
        try:
            varpathSTR = str(varfile)

            varPath = varfile
            backupPath = Path(varpathSTR + ArchiveInfo.VARBACKUPSUFFIX)

            backupMessagePrefix = "Error Backing up Var File:"

            if not os.path.exists(str(varPath)):
                time.sleep(1)

            if not os.path.exists(str(varPath)):
                raise Exception(
                    f"{backupMessagePrefix} The VarFile does not exist anymore - [{str(varPath)}]"
                )
            if os.path.exists(str(backupPath)):
                # backupfile already exists, delete backup file
                os.remove(backupPath)

            os.rename(str(varfile), str(backupPath))
        except FileExistsError as e:
            x = 1
        except Exception as e:
            errorQueue.put(f"Error Backing up Var File: [{varfile.name}]\n->{str(e)}")

    def replaceVarFileWithTempVar(
        self, varfile: Path, errorQueue: multiprocessing.Queue
    ):
        try:
            varPath = varfile
            varpathSTR = str(varfile)
            backupPath = Path(varpathSTR + ".tempvar")

            backupMessagePrefix = "Error Replacing Var File:"

            if not os.path.exists(str(varPath)):
                time.sleep(1)

            if not os.path.exists(str(varPath)):
                raise Exception(
                    f"{backupMessagePrefix} The VarFile does not exist anymore - [{str(varPath)}]"
                )

            if os.path.exists(varpathSTR) and os.path.exists(str(backupPath)):
                # varfile and tempfile exists, delete varfile and remove suffix from tempvar
                os.remove(varpathSTR)
                # backupPath.rename(backupPath.with_suffix(""))

        except Exception as e:
            errorQueue.put(
                f"Error Replacing varfile with tempvar: [{varfile.name}] \n-> [{backupPath.name}]\n->{str(e)}"
            )

    def optimizerSuccessCallback(self, param):
        # self.updateTaskbyOne()
        self.updateTotalProgressbyOne()

    def optimizerErrorCallback(self, param):
        # self.updateTaskbyOne()
        self.updateTotalProgressbyOne()
        Optimizer.postError(str(param))

    def optimizeVarFile(args: utils.ArgsDict):
        vF = args.varfile
        # scan varFile and index the contents
        if utils.validateVarFile(vF) is None:
            Optimizer.postError(f"[{str(vF)}] is not a valid var file!")
            return
        archiveinfo = ArchiveInfo(vF, imageConvertOption=args.options)
        tempZip = archiveinfo.createdTempArchive

        # repack-convert metadata
        print("metadata: " + str(vF))
        for metafile in archiveinfo.metaFiles:
            utils.convertRepackArchivedMetaFile(
                archive=zipfile.ZipFile(archiveinfo.archivePath, "r"),
                metafilePath=metafile.filename,
                targetArchive=archiveinfo.tempZip,
                errorQueue=args.errorQueue,
            )
        # repack jpg files

        # repack-convert other image files

        # rename original file to tempfile

        # rename repack to original file
        return

    def killAllProcesses(self):
        if self.processPool is not None:
            self.processPool.terminate()
