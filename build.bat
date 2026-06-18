@echo off

REM Switch to the directory where this script lives
cd /d "%~dp0"

echo ============================================
echo   智影溯源 - 桌面应用打包工具
echo ============================================
echo.
echo Working directory: %cd%
echo.

REM Check for Python 3.14
py -3.14 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.14 not found. This project requires Python 3.14.
    echo         Make sure Python 3.14 is installed and the "py" launcher is available.
    pause
    exit /b 1
)

REM Convert icon to ICO if needed (supports PNG and JPG)
if exist "%cd%\icon.png" (
    set ICON_SRC=%cd%\icon.png
) else if exist "%cd%\icon.jpg" (
    set ICON_SRC=%cd%\icon.jpg
) else (
    set ICON_SRC=
)

if defined ICON_SRC (
    if not exist "%cd%\icon.ico" (
        echo [1/3] Converting icon to icon.ico...
        py -3.14 -c "from PIL import Image; img = Image.open('%ICON_SRC%'); img.save('%cd%\icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Icon conversion failed, building without icon...
        ) else (
            echo        icon.ico created.
        )
    ) else (
        echo [1/3] icon.ico already exists, skipping conversion.
    )
) else (
    echo [1/3] No icon.png or icon.jpg found, building without custom icon.
)

REM Clean previous build
echo [2/3] Cleaning previous build...
if exist "%cd%\build" rmdir /s /q "%cd%\build"
if exist "%cd%\dist" rmdir /s /q "%cd%\dist"

REM Build EXE
echo [3/3] Building EXE with PyInstaller...
echo        This may take 10-30 minutes depending on system speed...
echo.
py -3.14 -m PyInstaller --clean --noconfirm "%cd%\app-entry.spec"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo   Build complete!
    echo   Output: dist\智影溯源.exe
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   Build FAILED! Check output above for errors.
    echo ============================================
)
pause
