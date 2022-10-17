@echo off
set name=var-optimizer

echo Activating Conda Environment ...
call conda activate ./.env

echo Packaging Project ...
pyinstaller ^
--windowed ^
--icon "img\icon.ico" ^
--name "%name%" ^
-y ^
"src\runme.py"

echo Deactivating Conda Environment ...
call conda deactivate
