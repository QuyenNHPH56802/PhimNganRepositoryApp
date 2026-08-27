@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: China-VNE pyVideoTrans Setup Script
:: ============================================================
:: Purpose: Install and configure pyVideoTrans v4.11 for
::          Chinese -> Vietnamese video translation.
:: Requirements: Windows 10/11, no Python needed (pre-packaged)
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
set "PYVIDEOTRANS_URL=https://huggingface.co/mortimerme/repocollect/resolve/main/win-pyvideotrans-v4.11.7z"
set "PYVIDEOTRANS_FILE=%ROOT_DIR%\win-pyvideotrans-v4.11.7z"
set "PYVIDEOTRANS_DIR=%ROOT_DIR%\pyvideotrans-win"

echo ============================================================
echo  China-VNE pyVideoTrans Setup
echo  Chinese to Vietnamese Video Translation
echo ============================================================
echo.

:: ----------------------------------------------------------
:: Step 1: Check prerequisites
:: ----------------------------------------------------------
echo [1/5] Checking prerequisites...

where curl >nul 2>&1
if errorlevel 1 (
    where wget >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] No download tool found. Please install curl or wget.
        echo         Download pyVideoTrans manually from:
        echo         https://github.com/jianchang512/pyvideotrans/releases
        goto :fail
    )
    set "DOWNLOAD_CMD=wget -O"
) else (
    set "DOWNLOAD_CMD=curl -L -o"
)

echo [PASS] Download tool available.
echo.

:: ----------------------------------------------------------
:: Step 2: Download pyVideoTrans
:: ----------------------------------------------------------
echo [2/5] Downloading pyVideoTrans v4.11 (~2.7 GB)...

if exist "%PYVIDEOTRANS_FILE%" (
    echo [INFO] File already exists: %PYVIDEOTRANS_FILE%
    set /p "CONFIRM=Overwrite? (y/N): "
    if /i not "!CONFIRM!"=="y" (
        echo Skipping download.
        goto :extract
    )
    del /f /q "%PYVIDEOTRANS_FILE%" 2>nul
)

echo Downloading from Hugging Face...
echo URL: %PYVIDEOTRANS_URL%
echo Save to: %PYVIDEOTRANS_FILE%
echo.

if defined DOWNLOAD_CMD (
    %DOWNLOAD_CMD% "%PYVIDEOTRANS_FILE%" "%PYVIDEOTRANS_URL%"
) else (
    echo [FAIL] No download tool available.
    goto :fail
)

if errorlevel 1 (
    echo [FAIL] Download failed.
    echo.
    echo Alternative download methods:
    echo   1. Baidu Netdisk: https://pan.baidu.com/s/1GkL4pyAYxJRvRor0jfh2rg
    echo   2. GitHub: https://github.com/jianchang512/pyvideotrans/releases
    echo.
    echo After download, place the .7z file in the project root.
    goto :manual
)

echo [PASS] Download complete.
echo.

:: ----------------------------------------------------------
:: Step 3: Extract
:: ----------------------------------------------------------
:extract
echo [3/5] Extracting archive...

if not exist "%PYVIDEOTRANS_FILE%" (
    echo [FAIL] Archive not found: %PYVIDEOTRANS_FILE%
    goto :manual
)

where 7z >nul 2>&1
if errorlevel 1 (
    where "C:\Program Files\7-Zip\7z.exe" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] 7-Zip not found. Please install 7-Zip:
        echo         https://www.7-zip.org/
        echo.
        echo Or use Bandizip / 360压缩:
        echo   1. Download the .7z file manually
        echo   2. Extract it to: %PYVIDEOTRANS_DIR%
        echo   3. Run setup_done.txt creation below
        goto :manual_extract
    )
    set "SEVENZIP=C:\Program Files\7-Zip\7z.exe"
) else (
    set "SEVENZIP=7z"
)

if exist "%PYVIDEOTRANS_DIR%" (
    echo [INFO] Removing old installation...
    rd /s /q "%PYVIDEOTRANS_DIR%" 2>nul
)

echo Extracting to: %PYVIDEOTRANS_DIR%
"%SEVENZIP%" x "%PYVIDEOTRANS_FILE%" -o"%PYVIDEOTRANS_DIR%" -y >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Extraction failed.
    goto :fail
)

echo [PASS] Extraction complete.
echo.

:: ----------------------------------------------------------
:: Step 4: Verify
:: ----------------------------------------------------------
echo [4/5] Verifying installation...

if not exist "%PYVIDEOTRANS_DIR%\sp.exe" (
    echo [FAIL] sp.exe not found in extracted folder.
    echo Expected: %PYVIDEOTRANS_DIR%\sp.exe
    goto :fail
)

echo [PASS] sp.exe found.
echo.

:: ----------------------------------------------------------
:: Step 5: Create setup marker
:: ----------------------------------------------------------
echo [5/5] Finalizing setup...

echo. > "%ROOT_DIR%\setup_done.txt"
echo China-VNE pyVideoTrans Setup > "%ROOT_DIR%\setup_done.txt"
echo Date: %DATE% %TIME% >> "%ROOT_DIR%\setup_done.txt"
echo Dir: %PYVIDEOTRANS_DIR% >> "%ROOT_DIR%\setup_done.txt"
echo Version: v4.11 >> "%ROOT_DIR%\setup_done.txt"

:: Check GPU
echo. >> "%ROOT_DIR%\setup_done.txt"
echo GPU Info: >> "%ROOT_DIR%\setup_done.txt"
nvidia-smi >> "%ROOT_DIR%\setup_done.txt" 2>&1
if errorlevel 1 (
    echo No NVIDIA GPU detected. >> "%ROOT_DIR%\setup_done.txt"
)

echo [PASS] Setup complete.
echo.
echo ============================================================
echo  Setup SUCCESSFUL
echo ============================================================
echo.
echo pyVideoTrans installed at:
echo   %PYVIDEOTRANS_DIR%
echo.
echo Next steps:
echo   1. Run: start.bat
echo   2. Configure API keys in the GUI
echo   3. Load a Chinese video and translate to Vietnamese
echo.
goto :end

:manual_extract
echo.
echo ============================================================
echo  Manual Extraction Required
echo ============================================================
echo.
echo Please extract the .7z file manually:
echo.
echo   1. Download: %PYVIDEOTRANS_FILE%
echo      or from: https://github.com/jianchang512/pyvideotrans/releases
echo.
echo   2. Extract to: %PYVIDEOTRANS_DIR%
echo      (do NOT extract to Desktop or Program Files)
echo.
echo   3. Ensure sp.exe is at: %PYVIDEOTRANS_DIR%\sp.exe
echo.
echo   4. Re-run this script or create:
echo      %ROOT_DIR%\setup_done.txt
echo.
goto :end

:manual
echo.
echo ============================================================
echo  Manual Download Required
echo ============================================================
echo.
echo Please download pyVideoTrans manually:
echo.
echo   Option 1 - Hugging Face (direct link):
echo   %PYVIDEOTRANS_URL%
echo.
echo   Option 2 - Baidu Netdisk:
echo   https://pan.baidu.com/s/1GkL4pyAYxJRvRor0jfh2rg
echo   Password: 1234
echo.
echo   Option 3 - GitHub releases:
echo   https://github.com/jianchang512/pyvideotrans/releases
echo.
echo Save the file as:
echo   %PYVIDEOTRANS_FILE%
echo.
echo Then re-run this script or manually extract.
goto :end

:fail
echo.
echo ============================================================
echo  Setup FAILED
echo ============================================================
echo.
echo Please check the error messages above.
echo For help, see docs/HUONG-DAN-CHINA-VIETNAM-A-Z.md
echo.

:end
endlocal
pause
