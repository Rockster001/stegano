@echo off
rem ============================================================
rem  Stegano - build ONE self-contained Stegano.exe (Windows)
rem  Double-click this file. The first build takes a few minutes.
rem  Later builds are faster.
rem ============================================================
cd /d "%~dp0"
echo.
echo [1/4] Checking Python 3.12 64-bit...
py -3.12-64 --version
if errorlevel 1 (
    echo.
    echo Python 3.12 64-bit was not found. Install it from python.org
    echo ^(tick "Add python.exe to PATH" during install^), then run this again.
    pause
    exit /b 1
)

echo.
echo [2/4] Creating the build environment ^(one-time, about a minute^)...
if not exist build_venv_312 py -3.12-64 -m venv build_venv_312
call build_venv_312\Scripts\activate.bat
python -c "import sys; assert sys.version_info[:2] == (3, 12) and sys.maxsize > 2**32"
if errorlevel 1 (
    echo.
    echo The build environment is not Python 3.12 64-bit.
    echo Remove build_venv_312 and run this file again.
    pause
    exit /b 1
)

echo.
echo [3/4] Installing pinned libraries...
python -m pip install --upgrade pip==26.1.1
if errorlevel 1 (
    echo.
    echo Updating pip FAILED - check your internet connection and try again.
    pause
    exit /b 1
)
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo.
    echo Library installation FAILED - check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo [4/4] Building Stegano.exe ^(this is the slow part, 3-5 minutes^)...
pyinstaller stegano.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo BUILD FAILED - take a photo of the last error lines above and ask your AI.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DONE!  Your program is here:
echo.
echo   %~dp0dist\Stegano.exe
echo.
echo   Notes:
echo   - The FIRST launch takes 10-30 seconds ^(it unpacks itself^).
echo     That is normal for a single-file program.
echo   - Windows may show a blue "Windows protected your PC" box the
echo     first time you run it: click "More info" then "Run anyway".
echo ============================================================
pause
