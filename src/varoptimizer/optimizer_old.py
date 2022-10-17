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
import io
import json
import multiprocessing
import os
import queue
import shutil
import threading
import time
import zipfile
from concurrent import futures
from concurrent.futures import process
from multiprocessing import context
from multiprocessing.pool import Pool
from pathlib import Path
from random import Random
from shutil import rmtree
from subprocess import call
from unittest import result
from zipfile import ZipFile, ZipInfo

import tqdm
from mpire import WorkerPool
from PIL import Image, ImageOps


def getAllFilesInDirByExtension(dir: str, extension=".zip", asString=False):
    hits = []
    for file in Path(dir).iterdir():
        if str(file).endswith(extension):
            if asString:
                file = str(file)
            hits.append(file)

    return hits


def printErrors(executionErrors: dict):
    errorcount = len(executionErrors.keys())
    if errorcount == 0:
        print("No Errors!")
    else:
        print(f"{errorcount} Errors:\n")
        for key, item in op.executionErrors:
            print(f"{key}\n\t")
            print(item)


def extractFileFromArchive(archive: ZipFile, file: ZipInfo, saveDirPath: Path):
    archive.extract(file, saveDirPath)
    return saveDirPath.joinpath(file.filename)


def isMetaFile(filepath: Path):
    if filepath.suffix.lower() in [".json", ".vap", ".vaj", ".vam"]:
        return True
    return False


def isImageFile(filepath: Path):
    if filepath.suffix.lower() in [".jpeg", ".png", ".jpg", ".tif", ".tiff"]:
        return True
    return False


def nya(tupl):
    # tupl = task,queue
    x = tupl[1]
    # Optimizer.convertArchivedImagetoTiffFromTask(tupl[0])
    # tupl[1].put(1)


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="The Directory to scan")
    parser.add_argument(
        "-r",
        help="Recursive Scan: Scall all subfolders",
        action="store_true",
    )
    parser.add_argument(
        "--resize",
        help="resizes the images: This number will be the max width/height of the image and preserves the Aspect Ratio",
        type=int,
    )
    args = parser.parse_args()
    return args


resultQ = queue.Queue()


class ImageConvertTask:
    def __init__(self, archive, imagePath, outdir, ImageSize, callback=None) -> None:
        self.archivePath = archive
        self.imagePath = imagePath
        self.outdir = outdir
        self.ImageSize = ImageSize
        self.callback = callback

    def run(self):
        Optimizer.convertArchivedImagetoTiff(
            self.archivePath, self.imagePath, self.outdir, self.ImageSize
        )

    def asDict(self):
        dd = {
            "archive": str(self.archivePath),
            "imagePath": str(self.imagePath),
            "outdir": str(self.outdir),
            "ImageSize": self.ImageSize,
            "callback": self.callback,
        }
        return dd

    def fromDict(self, my_dict):
        for key in my_dict:
            setattr(self, key, my_dict[key])
        return self

    def asMultiThreadTask(self):
        dd = self.asDict()
        return ImageConvertTask(
            dd["archive"],
            dd["imagePath"],
            dd["outdir"],
            dd["ImageSize"],
            dd["callback"],
        )


def iterdir2(
    dir: Path,
    asString=False,
    returnFullpath=True,
    recursive=False,
    returnRelativeToDir: Path = None,
):
    x = []
    if recursive:
        for root, dirs, files in os.walk(dir):
            for dir in dirs:
                for f in files:
                    x.append(os.path.join(root, f))
    else:
        for root, _, files in os.walk(dir):
            for f in files:
                x.append(os.path.join(root, f))

    if not returnFullpath:
        x = [str(Path(x).name) for x in x]

    if returnRelativeToDir is not None:
        x = [x.replace(str(returnRelativeToDir.resolve()), "") for x in x]

    if not asString:
        x = [Path(x) for x in x]

    return x


class OptimiserArgs:
    def __init__(self, resize) -> None:
        self.resize = int(resize) if resize > 0 else 0

    def asDict(self):
        return self.__dict__


class Optim:
    def launch(varfile, arg: OptimiserArgs):
        try:
            exec = Optim(varfile, arg)
            return "SUCCESS"
        except Exception as e:
            return f"FAILED - {e}"

    def __init__(self, varfile: Path, arg: OptimiserArgs) -> None:
        self.arg = arg
        self.varfile = varfile
        tempdir = self.extractArchive(varfile, Path(str(varfile) + "_tempdir"))
        imagePaths = self.getAllImagesInSubfolders(tempdir)
        metaPaths = self.getallMetaFilesInSubfolders(tempdir)
        self.convertAllPNGImageToTiff(imagePaths)
        self.updateTextureReferenceInMetafIles(metaPaths)
        packed = self.packFolderWith7Zip(tempdir, varfile)
        self.deleteTempDir(tempdir)
        self.backupVarFile(varfile)
        self.renameArchiveToVar(packed)

    def deleteTempDir(self, folderToDelete):
        shutil.rmtree(folderToDelete)

    def backupVarFile(self, varfile: Path):
        varfile.rename(str(varfile) + ".backup")

    def renameArchiveToVar(self, archive: Path):
        archive.rename(self.varfile)

    def extractArchive(self, archivePath, extractPath: Path):
        archive = py7zr.ZipFile(archivePath)
        if not extractPath.exists():
            extractPath.mkdir(parents=True)
        for zFile in archive.filelist:
            archive.extract(zFile, extractPath)
        return extractPath

    def getAllImagesInSubfolders(self, folder) -> list[Path]:
        files = iterdir2(folder, asString=False, returnFullpath=True, recursive=True)
        images = [
            file
            for file in files
            if file.suffix.lower() in [".jpg", ".png", ".tiff", ".jpeg"]
        ]
        return images

    def getallMetaFilesInSubfolders(self, folder) -> list[Path]:
        files = iterdir2(folder, asString=False, returnFullpath=True, recursive=True)
        metafiles = [
            file
            for file in files
            if file.suffix.lower() in [".json", ".vap", ".vaj", ".vam"]
        ]
        return metafiles

    def convertAllPNGImageToTiff(self, imagePaths: list[Path]):
        for imgPath in imagePaths:
            if imgPath.suffix == ".png":
                self.convertSingleImageToTiff(imgPath)
                os.remove(imgPath)

    def convertSingleImageToTiff(self, imgPath: Path):
        img = Image.open(imgPath)
        if self.arg.resize > 0:
            img = Optim.resizeImage(img, self.arg.resize)
        img.save(imgPath.with_suffix(".tiff"), compression="jpeg", quality=95)

    def resizeImage(self, image: Image.Image, newImageSize: int):
        return ImageOps.contain(image, (newImageSize, newImageSize))

    def updateTextureReferenceInMetafIles(self, metafiles):
        for metafile in metafiles:
            dump = open(metafile, encoding="utf8").read()
            newdump = dump.replace("png", "tiff")
            open(metafile, "w", encoding="utf8").write(newdump)

    def packFolderWith7Zip(self, folder: Path, varFile: Path):
        # the folder to pack <folder>_temp
        try:
            SevenZipExepath = r"C:\Program Files\7-Zip\7z.exe"
            zipargs = "a -tzip -bd -bso0 -m0=DEFLATE"
            parentFolder = folder.parent

            zipOutFullPath = parentFolder.joinpath(
                varFile.with_suffix(varFile.suffix + ".tempzip")
            )
            dirToZip = str(folder.joinpath("**"))
            sevenZipCommand = (
                f'{SevenZipExepath} {zipargs} "{str(zipOutFullPath)}" "{dirToZip}"'
            )
            if zipOutFullPath in iterdir2(parentFolder):
                os.remove(zipOutFullPath)
            result = call(sevenZipCommand)
            if result != 0:
                raise Exception(result)
            return Path(zipOutFullPath)
        except Exception as e:
            raise Exception("ERROR WHILE ZIPPING UP FILE:" + str(e))


class Optimizer:

    BACKUPSUFFIX = ".backup"
    newImageSize = 0
    executionErrors = {}

    def scanFolderForVars(dir):
        """
        first we need to find all var files that have its backupFile in the same directory
        then we delete the same-named var file, and rename the backupfile to var
        after that we can return these var files
        """
        allFilesInDir = [str(x) for x in Path(dir).iterdir() if x.is_file()]
        backupVarFiles: list[str] = []

        for f in getAllFilesInDirByExtension(dir, ".backup"):
            if Path(f).suffix == Optimizer.BACKUPSUFFIX:  # is this file a backup?
                backupVarFiles.append(f)

        for backupFile in backupVarFiles:
            originalVarFile = Path(backupFile).with_suffix("").__str__()
            if originalVarFile in allFilesInDir:
                os.remove(originalVarFile)
            Path(backupFile).rename(Path(backupFile).with_suffix("").__str__())

        return [Path(x) for x in getAllFilesInDirByExtension(dir, ".var")]

    def openArchivedBinaryImage(archivePath, imgSubPath: str):
        archive = ZipFile(str(archivePath), "r")
        imageBytes = io.BytesIO(archive.read(imgSubPath))
        return Image.open(imageBytes)

    def resizeImage(image: Image.Image, newImageSize: int):
        try:
            w = image.width
            h = image.height

            if newImageSize >= w or newImageSize >= h:
                return image

            return ImageOps.contain(image, (newImageSize, newImageSize))
        except Exception as e:
            raise Exception("ERROR WHILE RESIZING IMAGE: " + str(e))

    def convertArchivedImagetoTiff(archive, imgSubPath: str, outDir, newImageSize):
        try:
            image = Optimizer.openArchivedBinaryImage(archive, imgSubPath)
            imgPath = Path(imgSubPath)

            finalFileSavePath = outDir.joinpath(imgPath.with_suffix(".tiff"))

            Path(finalFileSavePath).parent.mkdir(parents=True, exist_ok=True)
            image = image.convert("RGBA", colors=256)
            # image.quantize(256, method=2)
            # image.mode = "RGBA"

            image = Optimizer.resizeImage(image, newImageSize)
            image.save(finalFileSavePath, compression="jpeg", quality=95)
        except Exception as e:
            raise Exception("ERROR WHILE CONVERTING IMAGE TO TIFF: " + str(e))

    def convertArchivedImagetoTiffFromTask(task: ImageConvertTask):
        try:
            Optimizer.convertArchivedImagetoTiff(
                task.archivePath, task.imagePath, task.outdir, task.ImageSize
            )
            task.callback()
            return "FINISHED"
        except Exception:
            return "CANCELLED"

    def convertArchivedImagetoJpeg(archive, imgSubPath: str, outDir):
        """Converting to jpeg\n
        return true if image was converted succesfully
        return false if image was not converted, because it contains a valid alpha channel
        """
        try:
            image = Optimizer.openArchivedBinaryImage(archive, imgSubPath)
            imgPath = Path(imgSubPath)
            print(imgSubPath)
            isAlphaNecessaray = Optimizer.isAlphaChannelNecessary(image)
            if isAlphaNecessaray:
                return False
            # jpeg Code here
            if image.mode != "RGB":
                image = image.convert("RGB")

            ramImage = io.BytesIO()
            image.save(ramImage, format="jpeg", quality=95, optimize=True)

            finalFileSavePath = outDir.joinpath(imgPath.with_suffix(".jpg"))
            Path(finalFileSavePath).parent.mkdir(parents=True, exist_ok=True)

            with open(finalFileSavePath, "wb") as file:
                file.write(ramImage.getbuffer())
            return True
        except Exception as e:
            raise ("ERROR WHILE CONVERTING ARCHIVED IMAGE TO JPG: " + str(e))

    def isAlphaChannelNecessary(image: Image.Image):
        if image.mode == "RGB":
            print("Valid alpha: NO - Image is 'RGB' ")
            return False

        if image.mode == "RGBA":
            alpha = image.split()[-1]
            Alphacolors = alpha.getcolors()
            pixels = {"white": 0, "black": 0, "grey": 0}
            for x in Alphacolors:
                color = x[1]
                if color > 128:
                    pixels["white"] += 1
                elif color < 128:
                    pixels["black"] += 1
                elif color == 128:
                    pixels["grey"] += 1
            pureBlackImage = pixels["white"] == 0 and pixels["black"] > 0
            pureWhiteImage = pixels["white"] > 0 and pixels["black"] == 0

            if pureWhiteImage:
                print("pure white alpha")
                return False
            elif pureBlackImage:
                print("pure Black alpha")
            else:
                print("mixed-color ALpha Image")
                return True

        return True

    # def extractFromZipIgnoreFiles(archive: ZipFile, ignoredFiles: list[ZipInfo], saveDirPath: Path):
    #     for f in archive.filelist:
    #         if f not in ignoredFiles:
    #             archive.extract(f, saveDirPath)

    def updateFileReferencesInJson(task: dict[Path, list[Path]]):
        file = next(iter(task))
        allFilesToConsider = [i.name for i in task[file]]
        lines = open(file, "r", encoding="utf8").readlines()
        dump = open(file, "r", encoding="utf8").read()

        jpeg = ".jpeg"
        jpg = ".jpg"
        png = ".png"
        tif = ".tif"
        tiff = ".tiff"

        # dump.replace(jpg, tiff)
        dump.replace(png, tiff)
        # dump.replace(tif, tiff)

        with open(file, "w") as writeFile:

            writeFile.write(dump)
        return

    def packfolderContentswith7zip(folder: Path, varname: str):
        # the folder to pack <folder>_temp
        try:
            SevenZipExepath = r"C:\Program Files\7-Zip\7z.exe"
            zipargs = "a -tzip -bd -bso0 -m0=DEFLATE"
            parentFolder = folder.parent

            zipOutFullPath = parentFolder.joinpath(varname).with_suffix(
                Path(varname).suffix + ".temp"
            )
            dirToZip = str(folder.joinpath("**"))
            sevenZipCommand = (
                f'{SevenZipExepath} {zipargs} "{str(zipOutFullPath)}" "{dirToZip}"'
            )
            if zipOutFullPath in iterdir2(parentFolder):
                os.remove(zipOutFullPath)
            result = call(sevenZipCommand)
            if result != 0:
                raise Exception(result)
            return Path(zipOutFullPath)
        except Exception as e:
            raise Exception("ERROR WHILE ZIPPING UP FILE:" + str(e))

    def OptimizeVarFile(self, varPath: Path, processPool: Pool):
        try:
            tempdir = varPath.with_name(varPath.stem + "_tempdir")
            tempdir.mkdir(parents=True, exist_ok=True)

            skippedImagesZipPaths: list[ZipInfo] = []
            varName = varPath.stem
            additionalSteps = 3

            with ZipFile(str(varPath.resolve()), "r") as archive:
                lenFilelist = len(archive.filelist)
                pbar = tqdm.tqdm(total=lenFilelist + additionalSteps, leave=False)

                # extract everything BUT png files
                pbar.set_description("Reading MetaData ...")
                for file in archive.filelist:
                    if Path(file.filename).suffix in [".png", ".tiff", ".tif"]:
                        skippedImagesZipPaths.append(file)
                pbar.update()

                pbar.set_description("Unzipping Files ...")
                for f in archive.filelist:
                    if f not in skippedImagesZipPaths:
                        extractFileFromArchive(archive, f, tempdir)
                        pbar.update()

                # extract&convert valid PNG's to jpegs
                pbar.set_description("Converting Images. Please Wait ...")
                imgConvertTasks: list[ImageConvertTask] = []

                def cockUpdate(var):
                    pbar.update()

                for imagePath in skippedImagesZipPaths:
                    imgConvertTasks.append(
                        ImageConvertTask(
                            varPath, imagePath.filename, tempdir, self.newImageSize
                        ).asMultiThreadTask()
                    )

                processPool.map_async(
                    Optimizer.convertArchivedImagetoTiffFromTask,
                    imgConvertTasks,
                    callback=cockUpdate,
                )

                # # oldprogress=pbar.3tal
                # finished = 0
                # while finished < len(imgConvertTasks):
                #     try:
                #         obj = resultQ.get_nowait()
                #     except queue.Empty:
                #         continue
                #     if obj is not None:
                #         finished += 1
                #         pbar.update()

            # change references for extracted Images in all manifests
            pbar.set_description_str("Updating MetaData ...")
            allFilesInAllSubdirsRelative = iterdir2(
                tempdir, asString=False, recursive=True, returnRelativeToDir=tempdir
            )
            allFilesInAllSubdirs = iterdir2(
                tempdir,
                asString=False,
                recursive=True,
            )

            allMetaFiles = [x for x in allFilesInAllSubdirs if isMetaFile(x)]
            allImageFiles = [x for x in allFilesInAllSubdirsRelative if isImageFile(x)]
            tasks = []

            for m in allMetaFiles:
                tasks.append({m: allImageFiles})
            processPool.map(Optimizer.updateFileReferencesInJson, tasks)

            # Optimizer.updateFileReferencesInJsons(
            #     tempdir, skippedImagesZipPaths)
            pbar.update()

            # pack with 7zip
            pbar.set_description("Finishing Up ...")
            packed = Optimizer.packfolderContentswith7zip(tempdir, varName)

            # rename old var file
            varPath.rename(varPath.with_suffix(".var.backup"))

            # rename zipped file to old var file
            newName = packed.with_suffix(".var")
            packed.rename(newName)

            # remove temp dir
            time.sleep(1)
            rmtree(tempdir)
            pbar.update()

        except Exception as e:
            self.executionErrors[varPath.name] = e
            if tempdir.exists():
                rmtree(tempdir)
        except KeyboardInterrupt as kI:
            processPool.join()

        return


def restoreBackupVars(inputdir):
    backupFileSuffix = ".backup"
    backupFiles = getAllFilesInDirByExtension(inputdir, ".var" + backupFileSuffix)
    varFiles = getAllFilesInDirByExtension(inputdir, ".var")

    # restore backups
    validBackups: dict[Path, Path] = {}
    for backupFile in backupFiles:
        for varfile in varFiles:
            strBackuFile = str(backupFile)
            if strBackuFile == str(varfile) + backupFileSuffix:
                validBackups[backupFile] = varfile

    for backup, original in validBackups.items():
        os.remove(original)
        backup.rename(backup.with_suffix(""))

    return getAllFilesInDirByExtension(inputdir, ".var")


def main():
    # main()
    title = "\n".join(
        [
            "=================================",
            "Smittys Var optimizer",
            "=================================",
        ]
    )

    # op = Optimizer()
    # op = Optim()
    processPool = Pool(4)
    args = parseArgs()
    inputdir = args.dir
    resize = args.resize

    if not os.path.exists(inputdir):
        print("INVALID DIRECTORY | DIRECTORY DOES NOT EXIST")
        return
    else:
        inputdir = Path(inputdir)

    varFiles = restoreBackupVars(inputdir)

    numberOfVars = len(varFiles)
    preTaskinfo = "Directory: " + str(inputdir) + os.linesep
    preTaskinfo += "Detected .var files: " + str(numberOfVars) + os.linesep

    print(title)
    print(preTaskinfo)

    # launching optimisation task
    with WorkerPool(n_jobs=4, keep_alive=True) as pool:
        args = [[vfile, OptimiserArgs(resize)] for vfile in varFiles]
        pool.map(
            Optim.launch,
            args,
            progress_bar=True,
            progress_bar_options={
                "desc": "Optimizing...",
                "unit": "var",
                "colour": "green",
            },
        )

    # prog = tqdm.tqdm(total=numberOfVars,postfix=)
    # for vfile in varFiles:
    #     prog.desc = "Optimizing ..."
    #     prog.set_postfix_str(vfile.name)
    #     op.OptimizeVarFile(vfile, processPool)
    #     prog.update()

    # region old multi task
    # with multiprocessing.Pool() as pool:
    #     r = list(
    #         tqdm.tqdm(pool.imap(op.OptimizeVarFile, varFiles), total=numberOfVars))
    # for _ in tqdm.tqdm(pool.imap_unordered(op.OptimizeVarFile, varFiles), desc="Optimizing ...", total=numberOfVars):
    #     pass
    # endregion

    print("Done!")

    # printErrors(op.executionErrors)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()


########################################################################
# originally in: optimizer.py

# def optimizeFolder(self, args: OptimizerArgs):
#       vF = args.varfile
# # scan varFile and index the contents
# if utils.validateVarFile(vF) is None:
#     Optimizer.postError(f"[{str(vF)}] is not a valid var file!")
#     return

# tempZip = archiveinfo.createdTempArchive

# # repack-convert metadata
# print("metadata: " + str(vF))
# for metafile in archiveinfo.metaFiles:
#     utils.convertRepackArchivedMetaFile(
#         archive=zipfile.ZipFile(archiveinfo.archivePath, "r"),
#         metafilePath=metafile.filename,
#         targetArchive=archiveinfo.tempZip,
#         errorQueue=args.errorQueue,
#     )

# for filepath in varFiles:
#     self.optimizeVarFile(filepath, args)

# """
# SC task1: scan all Archive Files and index their Contents
# """
# self.setUiNewTaskStatus(1, "Scanning Archives ...")
# task1 = []
# archiveInfos: list[ArchiveInfo] = []
# for vF in varFiles:
#     try:
#         archiveInfos.append(
#             ArchiveInfo(vF, imageConvertOption=args.optimizerOptions)
#         )
#     except Exception:
#         continue

# self.updateTotalProgressbyOne()
# self.updateTaskbyOne()

# """
#  multiP-task2 - extracting-Convert MetaData
# """
# task2 = self.setupTask2(archiveInfos)

# for task in task2:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()
# self.updateTotalProgressbyOne()

# # multiP-task3 - extracting JPG Files
# task3 = self.setupTask3(archiveInfos)

# for task in task3:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()
# self.updateTotalProgressbyOne()

# # multiP-task4 - extract-Converting OtherImageFiles
# task4 = self.setupTask4(archiveInfos, args)

# for task in task4:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()

# # multiP-task5 - zipping Archives

# task5 = self.setupTask5(archiveInfos, self.chunksize)

# for task in task5:
#     if task.get():
#         self.updateTaskbyOne()

# self.updateTotalProgressbyOne()

# # task6 Renaming var files to backup, if restoreBackus is enabled

# task6 = self.setupTask6(archiveInfos, self.chunksize,
#                         args.restoreBackupVars)

# for task in task6:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()

# # task7 renaming zippedArchives to VAR
# task7 = []
# for archInf in archiveInfos:
#     task7.append(self.processPool.starmap_async(
#         utils.renameArchiveToVar,
#         [(archInf.createdTempArchive, archInf.archivePath,
#           self.errorQueue)], chunksize=self.chunksize
#     ))

# self.setUiNewTaskStatus(utils.calcProgressBarMaxInt(
#     task7), "Renaming New Files ...")

# for task in task7:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()
# self.updateTotalProgressbyOne()

# # task8 deleting temp dirs
# task8 = []
# for archInf in archiveInfos:
#     task8.append(self.processPool.map_async(
#         shutil.rmtree,
#         [archInf.tempDir], chunksize=1
#     ))

# self.setUiNewTaskStatus(utils.calcProgressBarMaxInt(
#     task8), "Deleting Temp Dirs ...")

# for task in task8:
#     if task.get():
#         self.updateTaskbyOne()
#     self.printErrorsFromQueue()
# self.updateTotalProgressbyOne()
################################################################################
