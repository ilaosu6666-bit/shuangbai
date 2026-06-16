@echo off
chcp 65001 >nul
echo ============================================
echo   智影溯源 - 桌面应用打包工具
echo ============================================
echo.

REM Check for Python 3.14 (required for torch/streamlit)
py -3.14 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.14 not found. This project requires Python 3.14.
    pause
    exit /b 1
)

REM Convert PNG icon to ICO if needed
if exist "icon.png" (
    if not exist "icon.ico" (
        echo [1/3] Converting icon.png to icon.ico...
        python -c "from PIL import Image; img = Image.open('icon.png'); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Icon conversion failed, building without icon...
        ) else (
            echo        icon.ico created.
        )
    ) else (
        echo [1/3] icon.ico already exists, skipping conversion.
    )
) else (
    echo [1/3] No icon.png found, building without custom icon.
)

REM Clean previous build
echo [2/3] Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build EXE
echo [3/3] Building EXE with PyInstaller...
echo        This may take 10-30 minutes depending on system speed...
echo.
py -3.14 -m PyInstaller --clean --noconfirm app-entry.spec

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
