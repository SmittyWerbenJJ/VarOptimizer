import multiprocessing
import os
import pathlib
import shutil
import subprocess
import zipfile
from pathlib import Path
from zipfile import ZipFile

# from zipfile import *


class ZipUtils:
    @staticmethod
    def create_archive(root_folder: Path, where_to_save_the_zip_file: Path):
        """
        Create a .zip archive from a folder to a filepath
        filepath must have a suffix, regardless it will create a zip/Deflate file
        """
        if root_folder is None or where_to_save_the_zip_file is None:
            raise Exception("Invalid Folders for making zip files")
        if os.path.exists(str(where_to_save_the_zip_file)):
            os.remove(where_to_save_the_zip_file)
        createdArchive = Path(shutil.make_archive(
            where_to_save_the_zip_file, "zip", root_folder))
        createdArchive.rename(createdArchive.with_suffix(""))
        return createdArchive

    @staticmethod
    def extractArchive(archivePath, extractPath: Path):
        archive = zipfile.ZipFile(archivePath)
        if not extractPath.exists():
            extractPath.mkdir(parents=True)
        for zFile in archive.filelist:
            archive.extract(zFile, extractPath)
        return extractPath

    @staticmethod
    def extractFromArchive(archivePath: Path, filesList: list[Path], extractRootFolder: Path, errorQueue: multiprocessing.Queue):
        try:
            archive = ZipFile(archivePath)
            for zFile in filesList:
                finalPath = extractRootFolder.joinpath(zFile)
                if not extractRootFolder.exists():
                    extractRootFolder.mkdir(parents=True)
                archive.extract(str(zFile), extractRootFolder)#finalPath.parent)
            return extractRootFolder
        except Exception as e:
            errorQueue.put(
                f"Error Extracting From Archive - [{archivePath.name}]\n->{str(e)}")

    @staticmethod
    def renameArchiveToVar(archivePath: Path, varfile: Path, errorQueue: multiprocessing.Queue):
        try:
            new_path = archivePath.with_name(varfile.name)
            if os.path.exists(new_path):
                os.remove(new_path)
            archivePath.rename(new_path)
        except Exception as e:
            errorQueue.put(
                f"Error Renaming Archive to Var - [{archivePath.name}]\n->{str(e)}")

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

    @staticmethod
    def filter_zip_info_list_by_suffix(zipinfoList: list[zipfile.ZipInfo], extensions: list[str]) -> list[zipfile.ZipInfo]:
        filterList = []
        for f in zipinfoList:
            if Path(f.filename).suffix in extensions:
                filterList.append(f)
        return filterList

    @staticmethod
    def get_archive_filelist_filtered_by_suffix(archivePath: Path, filters: list[str]):
        filteredFiles = []
        with ZipFile(archivePath) as archive:
            for file in archive.filelist:
                if pathlib.Path(file.filename).suffix in filters:
                    filteredFiles.append(file)
        return filteredFiles
