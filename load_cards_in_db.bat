@echo off
echo Importing cards
python -m flask import-csv
echo Importing finished
pause