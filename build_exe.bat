@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "LOG_FILE=%CD%\build_output.log"
set "EXE_PATH=%CD%\dist\PixelGuardian\PixelGuardian.exe"

echo ======================================== > "%LOG_FILE%"
echo Pixel Guardian 1.0.0 - Safe EXE Build >> "%LOG_FILE%"
echo Started: %DATE% %TIME% >> "%LOG_FILE%"
echo ======================================== >> "%LOG_FILE%"

echo ========================================
echo   Pixel Guardian 1.0.0 - Safe Builder
echo ========================================
echo.

call :check_file ".venv\Scripts\python.exe" "Virtual environment Python"
if errorlevel 1 goto :failed

call :check_file "run.py" "run.py"
if errorlevel 1 goto :failed

call :check_file "PixelGuardian.spec" "PyInstaller spec"
if errorlevel 1 goto :failed

call :check_file "version_info.txt" "Version information"
if errorlevel 1 goto :failed

call :check_file "assets\icons\pixel_guardian_icon.ico" "Program icon"
if errorlevel 1 goto :failed

call :check_file "ui\styles\app.qss" "Application stylesheet"
if errorlevel 1 goto :failed

echo [1/7] Creating a source backup...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$items = @('app','assets','core','infrastructure','ui','run.py','requirements.txt','PixelGuardian.spec','PixelGuardianInstaller.iss','version_info.txt','build_exe.bat','build_installer.bat','.gitignore','README.md');" ^
  "Compress-Archive -Path $items -DestinationPath 'PixelGuardian_source_backup.zip' -Force" ^
  >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] Source backup failed.
    goto :failed
)

echo [2/7] Checking Python source files...
".venv\Scripts\python.exe" -m compileall -q app core infrastructure ui run.py ^
  >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] Python syntax check failed.
    echo Open build_output.log for details.
    goto :failed
)

echo [3/7] Checking the main application import...
".venv\Scripts\python.exe" -c "from app.bootstrap import start_application; print('Main import OK')" ^
  >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] The application import test failed.
    echo Open build_output.log for details.
    goto :failed
)

echo [4/7] Checking PyInstaller...
".venv\Scripts\python.exe" -c "import PyInstaller; print(PyInstaller.__version__)" ^
  >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo PyInstaller is not installed. Installing it now...
    ".venv\Scripts\python.exe" -m pip install pyinstaller ^
      >> "%LOG_FILE%" 2>&1

    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed.
        goto :failed
    )
)

echo [5/7] Cleaning old build output only...
if exist "build" rmdir /s /q "build"
if exist "dist\PixelGuardian" rmdir /s /q "dist\PixelGuardian"

echo [6/7] Building Pixel Guardian...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean "PixelGuardian.spec" ^
  >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
    echo [ERROR] EXE build failed.
    echo Open build_output.log for details.
    goto :failed
)

echo [7/7] Verifying the generated EXE...
if not exist "%EXE_PATH%" (
    echo [ERROR] Build finished, but PixelGuardian.exe was not found.
    goto :failed
)

echo.
echo ========================================
echo Build completed successfully.
echo ========================================
echo.
echo Source backup:
echo %CD%\PixelGuardian_source_backup.zip
echo.
echo EXE:
echo %EXE_PATH%
echo.
echo Build log:
echo %LOG_FILE%
echo.
start "" "%CD%\dist\PixelGuardian"
pause
exit /b 0

:check_file
if not exist "%~1" (
    echo [ERROR] Missing %~2:
    echo %CD%\%~1
    echo Missing: %~1 >> "%LOG_FILE%"
    exit /b 1
)
exit /b 0

:failed
echo.
echo ========================================
echo Build stopped safely.
echo Your source files were not deleted.
echo Review:
echo %LOG_FILE%
echo ========================================
pause
exit /b 1
