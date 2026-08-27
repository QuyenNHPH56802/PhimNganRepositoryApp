@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: China-VNE pyVideoTrans Update Script
:: ============================================================
:: Purpose: Update pyVideoTrans to the latest version
::          while preserving local settings.
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
set "PYVIDEOTRANS_DIR=%ROOT_DIR%\pyvideotrans-win"
set "SETUP_DONE=%ROOT_DIR%\setup_done.txt"
set "PARAMS_FILE=%PYVIDEOTRANS_DIR%\videotrans\params.json"
set "BACKUP_DIR=%ROOT_DIR%\pyvideotrans-backup"

echo ============================================================
echo  China-VNE pyVideoTrans Update
echo ============================================================
echo.

:: ----------------------------------------------------------
:: Check if running
:: ----------------------------------------------------------
echo [1/4] Checking if pyVideoTrans is running...
echo.
tasklist /FI "IMAGENAME eq sp.exe" 2>nul | findstr /i "sp.exe" >nul
if not errorlevel 1 (
    echo [WARN] pyVideoTrans is currently running.
    echo.
    echo Please close pyVideoTrans before updating.
    echo.
    set /p "KILL_IT=Kill and continue? (y/N): "
    if /i "!KILL_IT!"=="y" (
        taskkill /F /IM sp.exe 2>nul
        timeout /t 2 >nul
        echo [OK] Process terminated.
    ) else (
        echo Update cancelled.
        goto :end
    )
) else (
    echo [OK] pyVideoTrans is not running.
)

:: ----------------------------------------------------------
:: Step 2: Backup current settings
:: ----------------------------------------------------------
echo.
echo [2/4] Backing up current settings...
echo.

if exist "%PARAMS_FILE%" (
    if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%" 2>nul
    set "BACKUP_FILE=%BACKUP_DIR%\params.json.backup.%DATE:~0,4%%DATE:~5,2%%DATE:~8,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
    set "BACKUP_FILE=!BACKUP_FILE: =0!"
    copy /Y "%PARAMS_FILE%" "!BACKUP_FILE!" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Could not backup params.json.
    ) else (
        echo [PASS] Settings backed up to:
        echo         !BACKUP_FILE!
    )
) else (
    echo [INFO] No params.json found. Skipping backup.
)

:: Also backup f5-tts voice references
if exist "%PYVIDEOTRANS_DIR%\f5-tts" (
    if exist "%BACKUP_DIR%\f5-tts" rd /s /q "%BACKUP_DIR%\f5-tts" 2>nul
    xcopy /E /Y "%PYVIDEOTRANS_DIR%\f5-tts" "%BACKUP_DIR%\f5-tts\" >nul 2>&1
    if not errorlevel 1 (
        echo [PASS] Voice clone references backed up.
    )
)

:: ----------------------------------------------------------
:: Step 3: Download new version
:: ----------------------------------------------------------
echo.
echo [3/4] Downloading pyVideoTrans v4.11...
echo.
echo NOTE: This script downloads the LATEST version.
echo       If you want a specific version, download manually from:
echo       https://github.com/jianchang512/pyvideotrans/releases
echo.

set "PYVIDEOTRANS_URL=https://huggingface.co/mortimerme/repocollect/resolve/main/win-pyvideotrans-v4.11.7z"
set "PYVIDEOTRANS_FILE=%ROOT_DIR%\win-pyvideotrans-v4.11.7z"

where curl >nul 2>&1
if not errorlevel 1 (
    set "DOWNLOAD_CMD=curl -L -o"
) else (
    where wget >nul 2>&1
    if not errorlevel 1 (
        set "DOWNLOAD_CMD=wget -O"
    ) else (
        echo [FAIL] No download tool available.
        goto :fail
    )
)

echo Downloading: %PYVIDEOTRANS_URL%
echo.
%DOWNLOAD_CMD% "%PYVIDEOTRANS_FILE%" "%PYVIDEOTRANS_URL%"
if errorlevel 1 (
    echo [FAIL] Download failed.
    goto :fail
)
echo [PASS] Download complete.

:: ----------------------------------------------------------
:: Step 4: Extract and restore
:: ----------------------------------------------------------
echo.
echo [4/4] Extracting new version...
echo.

where 7z >nul 2>&1
if errorlevel 1 (
    set "SEVENZIP=C:\Program Files\7-Zip\7z.exe"
) else (
    set "SEVENZIP=7z"
)

:: Remove old installation
if exist "%PYVIDEOTRANS_DIR%" (
    echo Removing old installation...
    rd /s /q "%PYVIDEOTRANS_DIR%" 2>nul
)

:: Extract
echo Extracting...
"%SEVENZIP%" x "%PYVIDEOTRANS_FILE%" -o"%PYVIDEOTRANS_DIR%" -y >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Extraction failed.
    goto :fail
)

:: Restore settings
if exist "!BACKUP_FILE!" (
    echo Restoring settings...
    copy /Y "!BACKUP_FILE!" "%PARAMS_FILE%" >nul 2>&1
    echo [PASS] Settings restored.
)

if exist "%BACKUP_DIR%\f5-tts" (
    xcopy /E /Y "%BACKUP_DIR%\f5-tts" "%PYVIDEOTRANS_DIR%\f5-tts\" >nul 2>&1
)

:: Update setup marker
echo. > "%SETUP_DONE%"
echo China-VNE pyVideoTrans Update >> "%SETUP_DONE%"
echo Date: %DATE% %TIME% >> "%SETUP_DONE%"
echo Dir: %PYVIDEOTRANS_DIR% >> "%SETUP_DONE%"
echo Version: v4.11 >> "%SETUP_DONE%"

echo.
echo ============================================================
echo  Update SUCCESSFUL
echo ============================================================
echo.
echo New version installed at:
echo   %PYVIDEOTRANS_DIR%
echo.
echo Settings restored from backup.
echo.
echo To start:
echo   scripts\china-vietnam\start.bat
echo.

goto :end

:fail
echo.
echo ============================================================
echo  Update FAILED
echo ============================================================
echo.
echo Please check the error messages above.
echo You can manually update by:
echo   1. Downloading from: https://github.com/jianchang512/pyvideotrans/releases
echo   2. Extracting to: %PYVIDEOTRANS_DIR%
echo   3. Restoring backup from: !BACKUP_FILE!
echo.

:end
endlocal
pause
