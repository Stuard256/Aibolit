@echo off
echo Importing vaccines
python -m flask import-vac-csv
echo Importing finished
pause