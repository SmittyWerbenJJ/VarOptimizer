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

import argparse
import chunk
import io
import multiprocessing
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from distutils import filelist
from io import *
from multiprocessing.pool import *
from multiprocessing.pool import AsyncResult
from pathlib import Path
from tkinter import N
from uuid import uuid1
from zipfile import ZipFile, ZipInfo

from eventHook import EventHook
from progressDialog import ProgressDialog
from utils.fileUtils import FileUtils
from utils.imageUtils import Image, ImageUtils
from utils.ziputils import ZipUtils
from vamOptimizerUtils import *
from vamOptimizerUtils import ArchiveInfo


class Optimizer:

    def __init__(self) -> None:
        self.errorQueue = multiprocessing.Queue()
        self.progressdialog: ProgressDialog = None
        self.processPool: Pool = None
        self.threadPool: ThreadPool = None
        self.encounteredErrors = 0

    def optimizeFolder(self, args: OptimizerArgs):
        inputdir = args.dir
        self.progressdialog: ProgressDialog = args.progressDialog
        self.initProgressBarOnStartup(self.progressdialog)
        varFiles: list[Path] = FileUtils.get_all_files_in_dir_by_extension(
            inputdir, ".var",recursive=args.recursive)

        # init vars
        CPUCores = max(1, os.cpu_count()-1)
        Optimizer.processPool = Pool(CPUCores)
        manager = multiprocessing.Manager()
        self.errorQueue = manager.Queue()
        chunksize = max(1, 1)  # int(len(varFiles)/CPUCores))
        self.encounteredErrors = 0

        taskAmount = 8

        if args.restoreBackupVars:
            backups = Optimizer.findBackupVarFiles(inputdir)
            Optimizer.restoreBackupVars(backups)

        # resetProgressBars
        self.progressdialog.setTotalProgressRangeMax.emit(taskAmount)
        self.progressdialog.setTotalProgressDescription.emit(
            "Optimizing "+str(len(varFiles))+" .Var Files ... ")

        # SC - SingleCore
        # MC - MultiCore
        # MT - MultiThread
        # archiveFiles: list[ArchiveInfo] = []

        # start

        """
        SC task1: scan all Archive Files and index their Contents
        """
        self.setUiNewTaskStatus(1, "Scanning Archives ...")
        task1 = []
        archiveInfos: list[ArchiveInfo] = []
        for vF in varFiles:
            aInf = ArchiveInfo(vF, imageConvertOption=args.optimizerOptions)
            archiveInfos.append(aInf)
        self.updateTotalProgressbyOne()
        self.updateTaskbyOne()

        """
         multiP-task2 - extracting-Convert MetaData
        """
        task2 = self.setupTask2(archiveInfos)

        for task in task2:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()
        self.updateTotalProgressbyOne()

        # multiP-task3 - extracting JPG Files
        task3 = self.setupTask3(archiveInfos)

        for task in task3:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()
        self.updateTotalProgressbyOne()

        # multiP-task4 - extract-Converting OtherImageFiles
        task4 = self.setupTask4(archiveInfos, args)

        for task in task4:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()

        # multiP-task5 - zipping Archives

        task5 = self.setupTask5(archiveInfos, chunksize)

        for task in task5:
            if task.get():
                self.updateTaskbyOne()

        self.updateTotalProgressbyOne()

        # task6 Renaming var files to backup

        task6 = self.setupTask6(archiveInfos, chunksize)

        for task in task6:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()

        # task7 renaming zippedArchives to VAR
        task7 = []
        for archInf in archiveInfos:
            task7.append(Optimizer.processPool.starmap_async(
                ZipUtils.renameArchiveToVar,
                [(archInf.createdTempArchive, archInf.archivePath,
                  self.errorQueue)], chunksize=chunksize
            ))

        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            task7), "Renaming New Files ...")

        for task in task7:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()
        self.updateTotalProgressbyOne()

        # task8 deleting temp dirs
        task8 = []
        for archInf in archiveInfos:
            task8.append(Optimizer.processPool.map_async(
                shutil.rmtree,
                [archInf.tempDir], chunksize=1
            ))

        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            task8), "Deleting Temp Dirs ...")

        for task in task8:
            if task.get():
                self.updateTaskbyOne()
            self.printErrorsFromQueue()
        self.updateTotalProgressbyOne()

        # all tasks finished
        self.progressdialog.setTotalProgress.emit(taskAmount)
        self.progressdialog.setTaskProgressRangeMax.emit(1)
        self.progressdialog.setTaskProgress.emit(1)
        self.progressdialog.setTaskProgresssDescription.emit(
            "Done ...")
        self.progressdialog.setTotalProgressDescription.emit(
            "Done ...")

        self.progressdialog.writeTextLine(
            "Finished with "+str(self.encounteredErrors)+" Errors")

    def setupTask2(self, archiveInfos: list[ArchiveInfo]) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            files = [x.filename for x in archInf.metaFiles]
            args = [
                (archInf.archivePath,
                 files,
                 archInf.tempDir,
                 self.errorQueue)
            ]
            asyncTask = Optimizer.processPool.starmap_async(
                convertExtractArchivedMetaFile, args
            )
            res.append(asyncTask)
        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            res), "extracting-Convert MetaData...")

        return res

    def setupTask3(self, archiveInfos: list[ArchiveInfo]) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            task3jpgFiles = [x.filename for x in archInf.jpgFiles]
            task3argsJPEG = [(archInf.archivePath,
                              task3jpgFiles,
                              archInf.tempDir,
                              self.errorQueue
                              )]

            task3allOtherFiles = [x.filename for x in archInf.allOtherFiles]
            task3argsOther = [(archInf.archivePath,
                               task3allOtherFiles,
                               archInf.tempDir,
                               self.errorQueue
                               )]

            res.append(Optimizer.processPool.starmap_async(
                ZipUtils.extractFromArchive, task3argsJPEG))

            res.append(Optimizer.processPool.starmap_async(
                ZipUtils.extractFromArchive, task3argsOther))

        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            res), "extracting JPG & other Files ...")

        return res

    def setupTask4(self, archiveInfos: list[ArchiveInfo], args: OptimizerArgs) -> list[AsyncResult]:
        res: list[AsyncResult] = []
        for archInf in archiveInfos:
            for img in archInf.imgFiles:
                task4args = [(archInf.archivePath, img.filename,
                              archInf.tempDir, args.optimizerOptions, self.errorQueue)]
                res.append(Optimizer.processPool.starmap_async(
                    convertExtractArchivedImage, task4args))

        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            res), "Converting Images ...")

        return res

    def setupTask5(self, archiveInfos: list[ArchiveInfo], chunksize: int):
        res = []
        for archInf in archiveInfos:
            task5args = [(archInf.tempDir, archInf.createdTempArchive)]
            res.append(Optimizer.processPool.starmap_async(
                ZipUtils.create_archive, task5args, chunksize=chunksize))

        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            res), "zipping Archives ...")

        return res

    def setupTask6(self, archiveInfos: list[ArchiveInfo], chunksize: int):
        res = []
        for archInf in archiveInfos:
            res.append(Optimizer.processPool.starmap_async(
                Optimizer.backupVarFile,
                [(archInf.archivePath, self.errorQueue)], chunksize=chunksize
            ))
        self.setUiNewTaskStatus(calcProgressBarMaxInt(
            res), "Backung Up Original Vars  ...")
        return res

    def initProgressBarOnStartup(self, progressdialog: ProgressDialog):
        progressdialog.resetAllProgressbars.emit()
        progressdialog.setTotalProgressRangeMax.emit(1)
        progressdialog.setTotalProgressDescription.emit(
            "Loading ...")
        progressdialog.setTaskProgresssDescription.emit("Loading ...")

    def postError(self, error: str):
        self.encounteredErrors += 1
        self.progressdialog.writeTextLine.emit(error)

    def printErrorsFromQueue(self):
        try:
            error = self.errorQueue.get_nowait()
            if error is not None:
                self.progressdialog.writeTextLine.emit(error)
        except Exception as e:
            pass

    def updateTaskbyOne(self):
        self.progressdialog.updateTaskProgress.emit(1)

    def updateTotalProgressbyOne(self):
        self.progressdialog.updateTotalProgress.emit(1)

    def setUiNewTaskStatus(self, maxProgressNumber: int, taskDescription: str):
        self.progressdialog .setTaskProgressRangeMax.emit(maxProgressNumber)
        self.progressdialog.resetTaskProgress.emit()
        self.progressdialog.setTaskProgresssDescription.emit(taskDescription)

    @ staticmethod
    def findBackupVarFiles(inputdir):
        backupfiles = FileUtils.get_all_files_in_dir_by_extension(
            inputdir, ArchiveInfo.VARBACKUPSUFFIX)
        return backupfiles

    @ staticmethod
    def restoreBackupVars(varBackups: list[Path]):
        for vBackup in varBackups:
            if vBackup.with_suffix("").exists():
                os.remove(vBackup.with_suffix(""))
            vBackup.rename(vBackup.with_suffix(""))

    @ staticmethod
    def backupVarFile(varfile: Path, errorQueue: multiprocessing.Queue):
        try:
            varpathSTR = str(varfile)
            if not os.path.exists(varpathSTR):
                time.sleep(1)
            varfile.rename(str(varfile)+ArchiveInfo.VARBACKUPSUFFIX)
        except Exception as e:
            errorQueue.put(
                f"Error Backing up Var File: [{varfile.name}]\n->{str(e)}")

    def killAllProcesses(self):
        if self.processPool is not None:
            self.processPool.terminate()
