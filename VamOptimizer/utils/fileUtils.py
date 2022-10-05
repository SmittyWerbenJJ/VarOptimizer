import os
from pathlib import Path


class FileUtils:

    @staticmethod
    def get_all_files_in_dir_by_extension(dir: Path, extension=".zip", asString=False, recursive=False):
        hits: list[Path] = []
        dirsToSearch = []

        if recursive == True:
            for root, dirs, _ in os.walk(str(dir)):
                for subDir in dirs:
                    dirsToSearch.append(Path(os.path.join(root, subDir)))
        else:
            dirsToSearch = [dir]

        for searchDir in dirsToSearch:
            for file in searchDir.iterdir():
                if str(file).endswith(extension):
                    hits.append(file)

        if asString:
            return [str(x) for x in hits]
        else:
            return hits
