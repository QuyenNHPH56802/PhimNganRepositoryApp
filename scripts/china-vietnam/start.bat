@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: China-VNE pyVideoTrans Start Script
:: ============================================================
:: Purpose: Start pyVideoTrans GUI with China -> Vietnam
::          defaults configured.
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
set "PYVIDEOTRANS_DIR=%ROOT_DIR%\pyvideotrans-win"
set "SETUP_DONE=%ROOT_DIR%\setup_done.txt"

echo ============================================================
echo  China-VNE pyVideoTrans Launcher
echo ============================================================
echo.

:: ----------------------------------------------------------
:: Check if setup was run
:: ----------------------------------------------------------
if not exist "%SETUP_DONE%" (
    echo [WARN] setup_done.txt not found.
    echo.
    echo It looks like pyVideoTrans has not been set up yet.
    echo.
    echo Run setup.bat first to install pyVideoTrans.
    echo.
    set /p "RUN_SETUP=Run setup.bat now? (Y/n): "
    if /i "!RUN_SETUP!"=="n" goto :end
    call "%SCRIPT_DIR%setup.bat"
    if errorlevel 1 goto :end
)

:: ----------------------------------------------------------
:: Verify sp.exe exists
:: ----------------------------------------------------------
if not exist "%PYVIDEOTRANS_DIR%\sp.exe" (
    echo [FAIL] sp.exe not found at:
    echo   %PYVIDEOTRANS_DIR%\sp.exe
    echo.
    echo Please run setup.bat to install pyVideoTrans.
    goto :fail
)

:: ----------------------------------------------------------
:: Detect GPU
:: ----------------------------------------------------------
echo [INFO] Checking GPU...
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [INFO] NVIDIA GPU detected.
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
) else (
    echo [INFO] No NVIDIA GPU detected. Will use CPU.
    echo        For GPU acceleration, install CUDA 12.8 + cuDNN 9.11
)

echo.

:: ----------------------------------------------------------
:: Check for video input
:: ----------------------------------------------------------
if not "%~1"=="" (
    echo [INFO] Video file specified: %~1
    if not exist "%~1" (
        echo [WARN] File not found: %~1
    )
)

echo.
echo ============================================================
echo  Starting pyVideoTrans...
echo ============================================================
echo.
echo Default China -> Vietnam configuration:
echo   Source:     Chinese (zh-cn)
echo   Target:     Vietnamese (vi)
echo   ASR:        FunASR (channel 4, best for Chinese)
echo   Translation: DeepSeek (channel 5)
echo   TTS:        Edge-TTS (channel 0, free)
echo   Voice:      vi-VN-HoaiMyNeural
echo.
echo To use these defaults, configure in the GUI:
echo   - Step 2 (STT): Recognition channel = FunASR-Chinese
echo   - Step 3 (Translate): Translation channel = DeepSeek
echo   - Step 4 (TTS): TTS channel = Edge-TTS
echo   - Step 4 (TTS): Voice role = vi-VN-HoaiMyNeural
echo.
echo ============================================================
echo.

:: ----------------------------------------------------------
:: Launch
:: ----------------------------------------------------------
start "" "%PYVIDEOTRANS_DIR%\sp.exe"

echo [OK] pyVideoTrans should be starting now.
echo.
echo If the window does not appear, check:
echo   1. Your antivirus may be blocking it
echo   2. The folder path should NOT contain Chinese characters
echo   3. Try running as Administrator
echo.
echo Full logs are in:
echo   %PYVIDEOTRANS_DIR%\logs\
echo.

goto :end

:fail
echo.
echo Press any key to exit...
pause >nul

:end
endlocal
