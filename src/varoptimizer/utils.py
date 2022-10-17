import io
import multiprocessing
import multiprocessing as mp
import os
import pathlib
import shutil
import zipfile
from bz2 import compress
from distutils.log import error
from enum import Enum
from itertools import starmap
from multiprocessing.pool import Pool
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import ftfy
from genericpath import isfile
from PIL import Image, ImageFile, ImageOps

ImageFile.LOAD_TRUNCATED_IMAGES = True

from varoptimizer.archiveInfo import ArchiveInfo

from .commonImports import *


def get_all_files_in_dir_by_extension(
    dir: Path, extension=".zip", asString=False, recursive=False
):
    hits: list[Path] = []
    dirsToSearch = []

    dirsToSearch = [dir]
    if recursive == True:
        for root, dirs, _ in os.walk(str(dir)):
            for subDir in dirs:
                dirsToSearch.append(Path(os.path.join(root, subDir)))

    for searchDir in dirsToSearch:
        for file in searchDir.iterdir():
            if str(file).endswith(extension):
                hits.append(file)

    if asString:
        return [str(x) for x in hits]
    else:
        return hits


def writeBytesToFile(FullFilePath: Path, data: bytes):

    FullFilePath.parent.mkdir(parents=True, exist_ok=True)
    FullFilePath.touch(exist_ok=True)
    FullFilePath.write_bytes(data)


def writeTextToFile(FullFilePath: Path, data: str):

    FullFilePath.parent.mkdir(parents=True, exist_ok=True)
    FullFilePath.touch(exist_ok=True)
    FullFilePath.write_text(data)


def deleteFile(file):
    if os.path.exists(file):
        os.remove(file)


def deleteFolder(folder):
    if os.path.isdir(folder) and os.path.exists(folder):
        shutil.rmtree(folder)


# endregion

# region Image Utils


def openImage(image):
    return Image.open(image)


def resizeImage(image: Image.Image, newImageSize: int):
    if image.width <= newImageSize or image.height <= newImageSize:
        return image
    return ImageOps.contain(image, (newImageSize, newImageSize))


def extractConvertArchivedImage(image):
    pass


class imgFormat(Enum):
    TIFF = ".tiff"


# endregion

# region utils


class ImgConvertOption:
    format = imgFormat.TIFF
    resize = False
    resizeDimensions = 4096


def validateVarFile(vfile: Path):
    try:
        # this will crash if zipfile is not valid
        zFile = zipfile.ZipFile(vfile)
        return vfile
    except zipfile.BadZipFile as e:
        return None


def validateVarFiles(varFiles: list[Path]):
    result: list[Path] = []
    for vfile in varFiles:
        if validateVarFile(vfile) is not None:
            result.append(vfile)
    return result


def readFileFromArchive(archive: ZipFile, fileInArchive):
    return io.TextIOWrapper(
        io.BytesIO(archive.read(fileInArchive)),
        encoding="utf8",
        errors="replace",
    )


def convertExtractArchivedMetaFile(
    archivePath: Path,
    metaPathInArchive: str,
    OutSaveDirPath: Path,
    errorQueue: mp.Queue,
):
    with zipfile.ZipFile(archivePath, "r") as archive:

        try:
            for metafilePath in metaPathInArchive:
                dstPath = OutSaveDirPath.joinpath(metafilePath)
                dstPath.parent.mkdir(parents=True, exist_ok=True)

                dstPath.touch()
                wrapper = readFileFromArchive(archive, metafilePath)
                data = wrapper.read().replace(".png", ".tiff")
                dstPath.write_bytes(data)

        except Exception as e:
            errorQueue.put(
                f"Error Converting MetaFile [{metafilePath}] from archive [{archivePath.name}]: "
                + str(e)
            )


def MP_ExtractConvertArchivedMetaFiles(
    cpus: Pool, archiveInfo: ArchiveInfo, errorQueue: multiprocessing.Queue
):
    args = []
    for metafile in archiveInfo.metaFiles:
        arg = {
            "metafile": metafile,
            "errorQueue": errorQueue,
            "archiveInfo": archiveInfo,
        }
        args.append(arg)

    res = cpus.map_async(convertRepackArchivedMetaFile, args)
    x = res.get()

    return


def convertRepackArchivedMetaFile(arg: dict):
    try:
        ainf: ArchiveInfo = arg["archiveInfo"]
        archive = arg["archiveInfo"].openArchiveForReading()
        targetArchive = arg["archiveInfo"].opentempZipForAppending()
        metafilePath = arg["metafile"]
        saveFilePath = ainf.tempDir.joinpath(metafilePath.filename)
        wrapper = readFileFromArchive(archive, metafilePath)

        saveFilePath.parent.mkdir(parents=True, exist_ok=True)

        with open(saveFilePath, "w", encoding="utf8", errors="replace") as outfile:
            while line := wrapper.readline():
                outfile.write(line.replace(".png", ".tiff"))
    except Exception as e:
        arg["errorQueue"].put(
            f"Error Convert-Repacking MetaFile [{arg['metafile'].filename}] from archive [{arg['archiveInfo'].archivePath.name}]: "
            + traceback.format_exc(e)
        )


def MP_ExtractOtherFilesMP(
    cpus: Pool, archiveInfo: ArchiveInfo, errorQueue: multiprocessing.Queue
):
    args = []
    for otherFile in archiveInfo.allOtherFiles:
        arg = {
            "otherFile": otherFile,
            "errorQueue": errorQueue,
            "archiveInfo": archiveInfo,
        }
        args.append(arg)

    res = cpus.map_async(ExtractOtherFile, args)
    x = res.get()

    return


def ExtractOtherFile(arg: dict):
    try:
        ainf: ArchiveInfo = arg["archiveInfo"]
        archive = arg["archiveInfo"].openArchiveForReading()
        # targetArchive = arg["archiveInfo"].opentempZipForAppending()
        otherfilePath = arg["otherFile"]

        savePath = ainf.tempDir.joinpath(otherfilePath.filename)
        savePath.parent.mkdir(parents=True, exist_ok=True)
        try:
            ZipFile.extract(archive, otherfilePath, ainf.tempDir)
        except:
            arg["eerrorQueue"].put(
                f"CAUGHT EXCEPTION - this will be IGNORED:\nwhile extracting 'other' file [{otherfilePath}]:\n{traceback.format_exc()}"
            )
        # writeBytesToFile(savePath, archive.read(otherfilePath))
    except Exception as e:
        arg["errorQueue"].put(
            f"Error Extracting Other-File [{arg['metafile'].filename}] from archive [{arg['archiveInfo'].archivePath.name}]: "
            + str(e)
        )


def MP_ExtractConvertImages(
    cpus: Pool,
    archiveInfo: ArchiveInfo,
    imgConvertOptions: ImgConvertOption,
    errorQueue: multiprocessing.Queue,
):
    args = []
    for imageFile in archiveInfo.imgFiles:
        arg = {
            "imageFile": imageFile,
            "errorQueue": errorQueue,
            "archiveInfo": archiveInfo,
            "imgConvertOptions": imgConvertOptions,
        }
        args.append(arg)

    res = cpus.map_async(ExtractConvertArchivedImage, args)
    x = res.get()

    return


def ExtractConvertArchivedImage(arg: dict):
    try:
        ainf: ArchiveInfo = arg["archiveInfo"]
        archive = arg["archiveInfo"].openArchiveForReading()
        targetArchive = arg["archiveInfo"].opentempZipForAppending()
        imageFilePath: ZipInfo = arg["imageFile"]
        imgConvertOptions: ImgConvertOption = arg["imgConvertOptions"]

        img = openImage(io.BytesIO(archive.read(imageFilePath)))
        img = img.convert("RGBA")
        if imgConvertOptions.resize == True:
            img = resizeImage(img, imgConvertOptions.resizeDimensions)

        newImageFilePath = ainf.tempDir.joinpath(imageFilePath.filename).with_suffix(
            ".tiff"
        )
        newImageFilePath.parent.mkdir(parents=True, exist_ok=True)
        img.save(newImageFilePath, format="tiff", compression="jpeg", quality=95)

    except Exception as e:
        arg["errorQueue"].put(
            f"Error Convert-Repacking Image-File [{arg['imageFile'].filename}] from archive [{arg['archiveInfo'].archivePath.name}]: {traceback.format_exc()}"
        )


def backupVarFile(archiveinfo: ArchiveInfo):
    newSuffix = ".var.backup"
    archiveinfo.archivePath.rename(archiveinfo.archivePath.with_suffix(newSuffix))


def finalizeTempVar(archiveinfo: ArchiveInfo):
    newSuffix = ""
    archiveinfo.tempZipPath.rename(archiveinfo.tempZipPath.with_suffix(newSuffix))


@dataclass()
class VarBackup:
    backupVarPath: Path
    actualVarPath: Path


@dataclass
class ArgsDict:
    varfile: Path
    dir: Path
    restoreBackups: bool
    options: ImgConvertOption
    errorQueue: mp.Queue


@dispatch(list)
def calcProgressBarMaxInt(listOfObjects: list):
    return len(listOfObjects) - 1


@dispatch(int)
def calcProgressBarMaxInt(maxValue: int):
    return max(1, maxValue - 1)


# endregion

# region utils


def create_archive_for_ArchiveInfo(archiveinfo: ArchiveInfo):
    create_archive(archiveinfo.tempDir, archiveinfo.tempZipPath)


def create_archive(root_folder: Path, where_to_save_the_zip_file: Path):
    """
    Create a .zip archive from a folder to a filepath
    filepath must have a suffix, regardless it will create a zip/Deflate file
    """
    if root_folder is None or where_to_save_the_zip_file is None:
        raise Exception("Invalid Folders for making zip files")
    if os.path.exists(str(where_to_save_the_zip_file)):
        os.remove(where_to_save_the_zip_file)

    createdArchive = zipfile.ZipFile(
        where_to_save_the_zip_file,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=-1,
    )
    files_to_zip: list[Path] = []
    for obj in root_folder.glob("**/*"):
        if obj.is_file():
            files_to_zip.append(obj)
    for f in files_to_zip:
        createdArchive.write(f, f.relative_to(root_folder))
    return createdArchive


def extractArchive(archivePath, extractPath: Path):
    archive = zipfile.ZipFile(archivePath)
    if not extractPath.exists():
        extractPath.mkdir(parents=True)
    for zFile in archive.filelist:
        archive.extract(zFile, extractPath)
    return extractPath


def extractFromArchive(
    archivePath: Path,
    filesList: list[Path],
    extractRootFolder: Path,
    errorQueue: multiprocessing.Queue,
):
    try:
        archive = ZipFile(archivePath)
        for zFile in filesList:
            finalPath = extractRootFolder.joinpath(zFile)
            if not extractRootFolder.exists():
                extractRootFolder.mkdir(parents=True)
            archive.extract(str(zFile), extractRootFolder)  # finalPath.parent)
        return extractRootFolder
    except Exception as e:
        errorQueue.put(
            f"Error Extracting From Archive - [{archivePath.name}]\n->{str(e)}"
        )


def renameArchiveToVar(
    archivePath: Path, varfile: Path, errorQueue: multiprocessing.Queue
):
    try:
        new_path = archivePath.with_name(varfile.name)
        if os.path.exists(new_path):
            os.remove(new_path)
        archivePath.rename(new_path)
    except Exception as e:
        errorQueue.put(
            f"Error Renaming Archive to Var - [{archivePath.name}]\n->{str(e)}"
        )


# def getArchiveInfo(archivePath: Path) -> ArchiveInfo:
#     """Returns the Archive and a Filelist

#     Args:
#         archivePath (Path): ArchivePath

#     Returns:
#         archiveInfo
#     """
#     archive = zipfile.ZipFile(archivePath)
#     filelist = [x.filename for x in archive.filelist]
#     return ArchiveInfo(archivePath=archivePath, filelist=filelist)

# def scanArchiveForContents(archivePath: Path):
#     archiveInfo = getArchiveInfo(archivePath)
#     fileslist = [x for x in archiveInfo.filelist]
#     return fileslist


def filter_zip_info_list_by_suffix(
    zipinfoList: list[zipfile.ZipInfo], extensions: list[str]
) -> list[zipfile.ZipInfo]:
    filterList = []
    for f in zipinfoList:
        if Path(f.filename).suffix in extensions:
            filterList.append(f)
    return filterList


def get_archive_filelist_filtered_by_suffix(archivePath: Path, filters: list[str]):
    filteredFiles = []
    with ZipFile(archivePath) as archive:
        for file in archive.filelist:
            if pathlib.Path(file.filename).suffix in filters:
                filteredFiles.append(file)
    return filteredFiles


# endregion
