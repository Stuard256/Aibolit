@echo off
echo Reseting db
python -m flask reset-db
echo Database reset succeed!
pause