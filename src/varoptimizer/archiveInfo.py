import os
import shutil
import uuid
import zipfile
from distutils import filelist
from pathlib import Path

from . import utils


class ArchiveInfo:
    metafileSuffixes = [".json", ".vap", ".vaj", ".vam"]
    TEMPVAREXTENSION = ".tempvar"
    VARBACKUPSUFFIX = ".backup"
    ImageSuffixList = [".png", ".tiff", ".tga"]

    def __init__(
        self,
        archivePath: Path,
        imageConvertOption: "utils.ImgConvertOption" = None,
    ):
        try:
            self.initialize(archivePath, imageConvertOption)
        except Exception as e:
            raise e

    def initialize(
        self,
        archivePath: Path,
        imageConvertOption: "utils.ImgConvertOption" = None,
    ):
        self.filelist: list[zipfile.ZipInfo] = []
        self.metaFiles: list[zipfile.ZipInfo] = []
        self.jpgFiles: list[zipfile.ZipInfo] = []
        self.allOtherFiles: list[zipfile.ZipInfo] = []
        self.imgFiles: list[zipfile.ZipInfo] = []
        self.archivePath = archivePath
        self.tempDir: Path
        self.tempZipPath: Path
        # self.tempZipPath:zipfile.ZipFile
        # self.archive: zipfile.ZipFile

        if imageConvertOption is None:
            raise Exception("ArchiveInfo needs ImageConvertOption")

        self.imgConvertOptions = imageConvertOption

        # self.generateFilelist()
        archive = zipfile.ZipFile(self.archivePath, "r")
        self.filelist = archive.filelist

        self.allOtherFiles = self.filelist
        # self.generateMetaDataList()
        self.metaFiles = utils.get_archive_filelist_filtered_by_suffix(
            self.archivePath, self.metafileSuffixes
        )

        # self.generateJpgList()
        self.jpgFiles = utils.filter_zip_info_list_by_suffix(self.filelist, [".jpg"])

        # self.genereateImageToBeConvertedList()
        self.imgFiles = utils.filter_zip_info_list_by_suffix(
            self.filelist, self.ImageSuffixList
        )

        # self.generateOtherFilesFilelist()
        allRecognizedIFiles = self.metaFiles + self.imgFiles  # + self.jpgFiles

        # get a list of all files(Names) that will be skipped during optimisation

        for recognizedFile in allRecognizedIFiles:
            for file in self.filelist:
                if recognizedFile.filename == file.filename:
                    self.allOtherFiles.remove(file)
                    break

        # create Temp ZIp
        tempZipFullSuffix = str(self.archivePath.suffix) + self.TEMPVAREXTENSION
        self.tempZipPath = self.archivePath.with_suffix(tempZipFullSuffix)
        # tempzip = self.createTempZip(self.tempZipPath)

        # create temp dir
        self.tempDir = self.archivePath.parent.joinpath("optimizeTemp")
        if os.path.exists(str(self.tempDir)):
            shutil.rmtree(str(self.tempDir))
        self.tempDir.mkdir(parents=True, exist_ok=True)

    def createTempZip(self, path):
        if os.path.exists(str(path)):
            utils.deleteFile(path)
        zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)

    def opentempZipForAppending(self):
        return zipfile.ZipFile(self.tempZipPath, "a", zipfile.ZIP_DEFLATED)

    def openArchiveForReading(self):

        return zipfile.ZipFile(self.archivePath, "r")
