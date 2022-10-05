import io
from dataclasses import dataclass
from enum import Enum
from multiprocessing import Queue
from pathlib import Path
from uuid import uuid4
from zipfile import ZipInfo

from multipledispatch import dispatch
from PyQt5.QtCore import QObject, pyqtSignal

from .utils.imageUtils import *
from .utils.ziputils import *


class UiCallbackHandler(QObject):
    updateUI = pyqtSignal()


class OptimizerArgs:
    progressDialog = None
    mainMenuDialog = None
    recursive=False

    def __init__(self) -> None:
        self.dir: Path = None
        self.restoreBackupVars: bool = True
        # self.uiProgressCallbackHandler = UiCallbackHandler
        self.optimizerOptions = ImgConvertOption()


@dataclass()
class VarBackup:
    backupVarPath: Path
    actualVarPath: Path


class imgFormat(Enum):
    TIFF = ".tiff"


class ImgConvertOption:
    format = imgFormat.TIFF
    resize = False
    resizeDimensions = 4096


class ArchiveInfo:
    metafileSuffixes = [".json", ".vap", ".vaj", ".vam"]
    TEMPVAREXTENSION = ".tempvar"
    VARBACKUPSUFFIX = ".backup"
    ImageSuffixList= [".png",".tiff",".tga"]
    def __init__(self, archivePath: Path, imageConvertOption: ImgConvertOption = None):
        self.filelist: list[ZipInfo] = []
        self.metaFiles: list[ZipInfo] = []
        self.jpgFiles: list[ZipInfo] = []
        self.allOtherFiles: list[ZipInfo] = []
        self.imgFiles: list[ZipInfo] = []
        self.archivePath: Path
        self.tempDir: Path
        self.createdTempArchive: Path

        self.archivePath = archivePath

        if imageConvertOption is None:
            raise Exception("ArchiveInfo needs ImageConvertOption")

        self.imgConvertOptions = imageConvertOption

        # self.generateTempDir()
        if self.archivePath.exists():
            self.tempDir = self.archivePath.parent.joinpath(
                "tmp-"+str(uuid4()))
            self.tempDir.mkdir(parents=True, exist_ok=True)

        # self.generateFilelist()
        self.filelist = ZipFile(self.archivePath).filelist

        # self.generateMetaDataList()
        self.metaFiles = ZipUtils.get_archive_filelist_filtered_by_suffix(
            self.archivePath, self.metafileSuffixes
        )

        # self.generateJpgList()
        self.jpgFiles = ZipUtils.filter_zip_info_list_by_suffix(
            self.filelist, [".jpg"])

        # self.genereateImageToBeConvertedList()
        self.imgFiles = ZipUtils.filter_zip_info_list_by_suffix(
            self.filelist, self.ImageSuffixList)

        # self.generateOtherFilesFilelist()
        allRecognizedItems = self.metaFiles + self.jpgFiles + self.imgFiles

        fileListNames = {x.filename: x for x in self.filelist}
        allRecognizedItemNames = [x.filename for x in allRecognizedItems]
        for filename, zipinfo in fileListNames.items():
            if filename not in allRecognizedItemNames:
                self.allOtherFiles.append(zipinfo)

        # self.generateCreatedTempArchiveName()
        tempZipPath = str(self.archivePath.suffix) + self.TEMPVAREXTENSION
        self.createdTempArchive = self.archivePath.with_suffix(tempZipPath)


@dispatch(list)
def calcProgressBarMaxInt(listOfObjects: list):
    return len(listOfObjects)-1


@dispatch(int)
def calcProgressBarMaxInt(maxValue: int):
    return max(1, maxValue-1)


def convertExtractArchivedImage(archivePath: Path, imgPathInArchive: str, OutSaveDirPath: Path, imgConvertOptions: ImgConvertOption, errorQueue: Queue):

    with ZipFile(archivePath, "r") as archive:
        try:
            imgbytes = io.BytesIO(archive.read(imgPathInArchive))
            img = Image.open(imgbytes)
            finalSavePath = OutSaveDirPath.joinpath(
                imgPathInArchive).with_suffix(".tiff")

            img = img.convert("RGBA")
            if imgConvertOptions.resize == True:
                img = ImageUtils.resizeImage(
                    img, imgConvertOptions.resizeDimensions)

            finalSavePath.parent.mkdir(parents=True, exist_ok=True)
            with finalSavePath.open("wb") as file:
                img.save(file, format="tiff", compression="jpeg", quality=95)

        except Exception as e:
            errorQueue.put("Error Converting Image from archive: "+str(e))


def convertExtractArchivedMetaFile(archivePath: Path, metaPathInArchive: str, OutSaveDirPath: Path, errorQueue: Queue):
    with ZipFile(archivePath, "r") as archive:
        try:
            for metafilePath in metaPathInArchive:
                dstPath = OutSaveDirPath.joinpath(metafilePath)
                dstPath.parent.mkdir(parents=True, exist_ok=True)

                outputFile = open(dstPath, "w",encoding="utf8")
                wrapper = io.TextIOWrapper(io.BytesIO(
                    archive.read(metafilePath)), encoding="utf8")

                data = wrapper.read().replace(".png", ".tiff")
                outputFile.write(data)
                outputFile.close()
        except Exception as e:
            errorQueue.put("Error Converting MetaFiles from archive: "+str(e))
