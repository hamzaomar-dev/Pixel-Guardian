@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "ISCC_LOCAL=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
set "ISCC_X86=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
set "ISCC_X64=%ProgramFiles%\Inno Setup 6\ISCC.exe"

set "SCRIPT=%CD%\PixelGuardianInstaller.iss"
set "EXE=%CD%\dist\PixelGuardian\PixelGuardian.exe"

echo ========================================
echo Pixel Guardian 1.0.0 - Installer Builder
echo ========================================
echo.

if not exist "%SCRIPT%" (
    echo [ERROR] Missing:
    echo %SCRIPT%
    pause
    exit /b 1
)

if not exist "%EXE%" (
    echo [ERROR] PixelGuardian.exe was not found:
    echo %EXE%
    echo Build the EXE first.
    pause
    exit /b 1
)

if not exist "assets\icons\pixel_guardian_icon.ico" (
    echo [ERROR] Installer icon was not found:
    echo %CD%\assets\icons\pixel_guardian_icon.ico
    pause
    exit /b 1
)

if exist "%ISCC_LOCAL%" (
    set "ISCC=%ISCC_LOCAL%"
) else if exist "%ISCC_X86%" (
    set "ISCC=%ISCC_X86%"
) else if exist "%ISCC_X64%" (
    set "ISCC=%ISCC_X64%"
) else (
    echo [ERROR] Inno Setup 6 was not found.
    echo Install Inno Setup 6, then run this file again.
    pause
    exit /b 1
)

echo Using Inno Setup:
echo %ISCC%
echo.

echo Building installer...
"%ISCC%" "%SCRIPT%"

if errorlevel 1 (
    echo.
    echo [ERROR] Installer build failed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installer created successfully:
echo %CD%\installer_output\PixelGuardian_Setup_1.0.0.exe
echo ========================================
echo.
start "" "%CD%\installer_output"
pause
exit /b 0