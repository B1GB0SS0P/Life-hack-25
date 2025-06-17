@echo off
set ZIP_FILE=searxng.zip
set DEST_FOLDER=searxng

REM Create destination folder if it doesn't exist
if not exist "%DEST_FOLDER%" (
    mkdir "%DEST_FOLDER%"
)

REM Use PowerShell Expand-Archive to unzip
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%DEST_FOLDER%' -Force"

echo Extraction complete.
docker build -t searxng:custom .