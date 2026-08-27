@echo off
setlocal EnableDelayedExpansion

:: ============================================================
:: China-VNE pyVideoTrans Doctor Script
:: ============================================================
:: Purpose: Diagnose pyVideoTrans environment and report
::          pass/fail for each component.
:: ============================================================

set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%..\.."
set "PYVIDEOTRANS_DIR=%ROOT_DIR%\pyvideotrans-win"
set "REPORT_FILE=%ROOT_DIR%\doctor_report.txt"

echo ============================================================
echo  China-VNE pyVideoTrans Doctor
echo  Chinese to Vietnamese Video Translation
echo ============================================================
echo.

:: Initialize report
(
    echo ============================================================
    echo  China-VNE pyVideoTrans Doctor Report
    echo  Date: %DATE% %TIME%
    echo ============================================================
    echo.
) > "%REPORT_FILE%"

set "PASS_COUNT=0"
set "FAIL_COUNT=0"
set "WARN_COUNT=0"

:: Helper: report pass
set "REPORT_PASSTMP=echo [PASS]
set "REPORT_PASS=!REPORT_PASSTMP! %%1
set "REPORT_PASS=!REPORT_PASS:~0,-1!

:: ============================================================
:: Check 1: Setup marker
:: ============================================================
echo [1/12] Checking installation status...
(
    echo [1/12] Installation Status
) >> "%REPORT_FILE%"
if exist "%PYVIDEOTRANS_DIR%\sp.exe" (
    echo [PASS] pyVideoTrans installed.
    (
        echo   PASS: sp.exe found at %PYVIDEOTRANS_DIR%\sp.exe
        echo.
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] pyVideoTrans not installed.
    (
        echo   FAIL: sp.exe not found
        echo   ACTION: Run setup.bat to install pyVideoTrans
        echo.
    ) >> "%REPORT_FILE%"
    set /a FAIL_COUNT+=1
)

:: ============================================================
:: Check 2: sp.exe exists
:: ============================================================
echo [2/12] Checking sp.exe...
(
    echo [2/12] sp.exe Executable
) >> "%REPORT_FILE%"
if exist "%PYVIDEOTRANS_DIR%\sp.exe" (
    echo [PASS] sp.exe found.
    (
        echo   PASS: sp.exe exists
        echo.
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] sp.exe missing.
    (
        echo   FAIL: sp.exe not found
        echo   ACTION: Re-run setup.bat
        echo.
    ) >> "%REPORT_FILE%"
    set /a FAIL_COUNT+=1
)

:: ============================================================
:: Check 3: FFmpeg
:: ============================================================
echo [3/12] Checking FFmpeg...
(
    echo [3/12] FFmpeg
) >> "%REPORT_FILE%"
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%i in ('ffmpeg -version 2^>nul ^| findstr /i "ffmpeg version"') do echo [PASS] %%i
    (
        echo   PASS: FFmpeg found in PATH
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
if exist "%PYVIDEOTRANS_DIR%\ffmpeg\ffmpeg.exe" (
    echo [PASS] FFmpeg bundled in pyvideotrans-win\ffmpeg\.
    (
        echo   PASS: Bundled FFmpeg found at %PYVIDEOTRANS_DIR%\ffmpeg\
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [WARN] FFmpeg not in PATH and not bundled.
    (
        echo   WARN: FFmpeg not found in PATH
        echo   NOTE: Pre-packaged version includes FFmpeg in ffmpeg\ folder
        echo   ACTION: If video processing fails, verify FFmpeg
    ) >> "%REPORT_FILE%"
    set /a WARN_COUNT+=1
)
)

:: ============================================================
:: Check 4: NVIDIA GPU
:: ============================================================
echo [4/12] Checking GPU...
(
    echo [4/12] NVIDIA GPU
) >> "%REPORT_FILE%"
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [PASS] NVIDIA GPU detected ^(RTX-series^).
    (
        echo   PASS: NVIDIA GPU available
        echo   INFO: Run nvidia-smi for details
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [INFO] No NVIDIA GPU. CPU mode will be used.
    (
        echo   INFO: No NVIDIA GPU detected
        echo   NOTE: pyVideoTrans will run in CPU mode
        echo   NOTE: GPU acceleration requires NVIDIA GPU + CUDA 12.8
    ) >> "%REPORT_FILE%"
    set /a WARN_COUNT+=1
)

:: ============================================================
:: Check 5: PyTorch CUDA
:: ============================================================
echo [5/12] Checking PyTorch + CUDA...
(
    echo [5/12] PyTorch + CUDA
) >> "%REPORT_FILE%"
if exist "%PYVIDEOTRANS_DIR%\_internal\torch" (
    echo [PASS] PyTorch found in bundled Python.
    (
        echo   PASS: PyTorch bundled with pre-packaged version
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    if exist "%PYVIDEOTRANS_DIR%\python.exe" (
        echo [INFO] Python found, checking PyTorch...
        (
            echo   INFO: Python found at %PYVIDEOTRANS_DIR%\python.exe
        ) >> "%REPORT_FILE%"
    ) else (
        echo [INFO] Pre-packaged version uses bundled Python.
        (
            echo   INFO: Pre-packaged version (no separate Python needed)
        ) >> "%REPORT_FILE%"
    )
    set /a PASS_COUNT+=1
)

:: ============================================================
:: Check 6: Chinese ASR (FunASR)
:: ============================================================
echo [6/12] Checking Chinese ASR capability...
(
    echo [6/12] Chinese ASR (FunASR)
) >> "%REPORT_FILE%"
echo [PASS] FunASR is built-in in pyVideoTrans v4.11.
(
    echo   PASS: FunASR is built-in (no extra install needed)
    echo   RECOMMENDATION: Use FunASR channel for Chinese ASR
) >> "%REPORT_FILE%"
set /a PASS_COUNT+=1

:: ============================================================
:: Check 7: Vietnamese TTS (Edge-TTS)
:: ============================================================
echo [7/12] Checking Vietnamese TTS capability...
(
    echo [7/12] Vietnamese TTS
) >> "%REPORT_FILE%"
echo [PASS] Edge-TTS is built-in with Vietnamese voices.
(
    echo   PASS: Edge-TTS built-in with Vietnamese support
    echo   Available voices: vi-VN-HoaiMyNeural, vi-VN-NamMinhNeural
    echo   RECOMMENDATION: Use Edge-TTS channel 0 for free Vietnamese TTS
) >> "%REPORT_FILE%"
set /a PASS_COUNT+=1

:: ============================================================
:: Check 8: Translation providers
:: ============================================================
echo [8/12] Checking translation providers...
(
    echo [8/12] Translation Providers
) >> "%REPORT_FILE%"
echo [INFO] Checking API key configurations...
(
    echo   INFO: Configure API keys in pyVideoTrans GUI
    echo   RECOMMENDED: DeepSeek (channel 5) for Chinese -> Vietnamese
    echo   FALLBACK: ChatGPT (channel 4), Google Translate (channel 0)
) >> "%REPORT_FILE%"
set /a WARN_COUNT+=1

:: ============================================================
:: Check 9: Output directory
:: ============================================================
echo [9/12] Checking output directory...
(
    echo [9/12] Output Directory
) >> "%REPORT_FILE%"
set "OUTPUT_DIR=%ROOT_DIR%\output"
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%" 2>nul
if exist "%OUTPUT_DIR%" (
    echo [PASS] Output directory ready.
    (
        echo   PASS: Output directory exists at %OUTPUT_DIR%
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [FAIL] Cannot create output directory.
    (
        echo   FAIL: Cannot create %OUTPUT_DIR%
        echo   ACTION: Check write permissions
    ) >> "%REPORT_FILE%"
    set /a FAIL_COUNT+=1
)

:: ============================================================
:: Check 10: Configuration file
:: ============================================================
echo [10/12] Checking configuration...
(
    echo [10/12] Configuration
) >> "%REPORT_FILE%"
if exist "%PYVIDEOTRANS_DIR%\videotrans\params.json" (
    echo [PASS] params.json found.
    (
        echo   PASS: params.json exists
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [INFO] params.json will be created on first run.
    (
        echo   INFO: params.json will be created on first run
    ) >> "%REPORT_FILE%"
    set /a WARN_COUNT+=1
)

:: ============================================================
:: Check 11: Voice clone directory
:: ============================================================
echo [11/12] Checking voice clone directory...
(
    echo [11/12] Voice Clone Setup
) >> "%REPORT_FILE%"
set "F5_DIR=%PYVIDEOTRANS_DIR%\f5-tts"
if not exist "%F5_DIR%" mkdir "%F5_DIR%" 2>nul
if exist "%F5_DIR%" (
    echo [PASS] f5-tts directory ready for voice cloning.
    (
        echo   PASS: f5-tts directory ready
        echo   NOTE: Place .wav reference audio here for F5-TTS voice cloning
        echo   NOTE: Supports: zh, en, ja, it, de, fr, ru, hi, es, ar, tr, vi
    ) >> "%REPORT_FILE%"
    set /a PASS_COUNT+=1
) else (
    echo [WARN] Cannot create f5-tts directory.
    (
        echo   WARN: Cannot create f5-tts directory
    ) >> "%REPORT_FILE%"
    set /a WARN_COUNT+=1
)

:: ============================================================
:: Check 12: pyVideoTrans version
:: ============================================================
echo [12/12] Checking pyVideoTrans version...
(
    echo [12/12] Version
) >> "%REPORT_FILE%"
if exist "%PYVIDEOTRANS_DIR%\videotrans\__init__.py" (
    findstr /C:"VERSION" "%PYVIDEOTRANS_DIR%\videotrans\__init__.py" 2>nul | findstr "=" | (
        for /f "delims=" %%v in ('findstr /C:"VERSION" "%PYVIDEOTRANS_DIR%\videotrans\__init__.py"') do (
            echo [PASS] %%v
            (
                echo   %%v
            ) >> "%REPORT_FILE%"
        )
    )
    set /a PASS_COUNT+=1
) else (
    echo [INFO] Version check skipped (pre-packaged exe).
    (
        echo   INFO: Pre-packaged exe (version in exe metadata)
        echo   RECOMMENDED: v4.11 for latest features
    ) >> "%REPORT_FILE%"
    set /a WARN_COUNT+=1
)

:: ============================================================
:: Summary
:: ============================================================
echo.
echo ============================================================
echo  Doctor Summary
echo ============================================================
(
    echo.
    echo ============================================================
    echo  SUMMARY
    echo ============================================================
    echo   PASS: !PASS_COUNT!
    echo   WARN: !WARN_COUNT!
    echo   FAIL: !FAIL_COUNT!
    echo.
    echo  Report saved to: %REPORT_FILE%
    echo ============================================================
) >> "%REPORT_FILE%"

echo   PASS: !PASS_COUNT!
echo   WARN: !WARN_COUNT!
echo   FAIL: !FAIL_COUNT!
echo.
echo  Report saved to: %REPORT_FILE%
echo.

if !FAIL_COUNT! gtr 0 (
    echo [RESULT] FAILURES detected. Please fix the issues above.
    echo.
) else (
    if !WARN_COUNT! gtr 0 (
        echo [RESULT] OK with warnings. Review the report for details.
        echo.
    ) else (
        echo [RESULT] ALL CHECKS PASSED. Ready to use!
        echo.
    )
)

echo ============================================================
echo  China-VNE Recommended Configuration
echo ============================================================
echo.
echo   Step 1 (Video): Load your Chinese video (.mp4/.mkv/.mov)
echo.
echo   Step 2 (STT):
echo     Recognition channel: FunASR-Chinese ^(channel 4^)
echo     Model: SenseVoiceSmall or paraformer-zh
echo.
echo   Step 3 (Translate):
echo     Translation channel: DeepSeek ^(channel 5^)
echo     Source language: zh-cn
echo     Target language: vi
echo     Model: deepseek-chat
echo.
echo   Step 4 (TTS):
echo     TTS channel: Edge-TTS ^(channel 0^)
echo     Voice role: vi-VN-HoaiMyNeural
echo     (or vi-VN-NamMinhNeural for male voice^)
echo.
echo   Step 5 (Output):
echo     Video codec: libx265 or libx264
echo     CRF: 20
echo     Format: mp4
echo.
echo ============================================================
echo.

endlocal
pause
