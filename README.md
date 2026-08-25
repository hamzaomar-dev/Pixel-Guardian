Pixel Guardian

Pixel Guardian is a Windows desktop utility for monitoring PC hardware and system activity, reviewing drivers and disk health, safely cleaning temporary files, and checking gaming readiness from a single interface.

Built as a complete desktop product using a layered Python architecture, Pixel Guardian combines Windows system information, real-time monitoring, maintenance tools, and gaming-focused utilities in one application.

Current version: 1.0.0

Screenshots

Dashboard



Hardware Information



Live Monitor



Game Lab



Drivers



Cleaner



Features

Hardware Information

Windows and operating-system information

CPU model and core information

Installed and available memory

Graphics-card information

Motherboard and BIOS information

Storage and other detected hardware details

Live Monitor

Real-time CPU usage

Memory usage

System-drive usage

Running-process count

Disk activity

Network activity

Per-core CPU utilization

Pause and resume monitoring

Disk Health

Detects installed drives

Displays drive type, capacity, firmware, and operational status

Reads supported Windows disk-health and reliability information

Supports additional reliability information when Windows permissions and hardware support allow it

Drivers

Scans installed Windows devices and drivers

Displays device class, status, version, provider, date, and signature state

Highlights devices that may require attention

Supports searching and filtering the driver inventory

Quick access to Windows Device Manager

Safe Cleaner

Scans before deleting anything

Detects temporary and unnecessary files

Separates standard and administrator-required cleanup operations

Shows detected size and item count before cleaning

Supports categories such as user temporary files, Windows temporary files, thumbnail cache, DirectX shader cache, and other supported cleanup targets

Game Lab

Detects supported installed Steam and Epic Games

Reviews Windows gaming-readiness settings

Detects the current CPU and GPU for gaming-performance checks

Supports online FPS estimates through FPSHQ when data is available

Caches successful gaming-performance results locally

Application Settings

English and Arabic interface support

Restore last opened page

Windows notifications

Notification sound controls

System-tray support

Start minimized and tray behavior

Tech Stack

Python 3.12

PySide6 / Qt — desktop UI

psutil — system and performance metrics

Windows system APIs / Registry / PowerShell integration

PyInstaller — Windows application packaging

Inno Setup 6 — Windows installer

Architecture

Pixel Guardian uses a layered structure that separates application logic, Windows-specific system access, and the UI.

app/              Application bootstrap and startup
core/             Domain models and application services
infrastructure/   Windows providers, logging, paths, and elevation
ui/               PySide6 pages, widgets, navigation, and styles
assets/           Application icons and visual assets

This structure keeps Windows-specific operations inside infrastructure providers while UI pages communicate through application services.

Project Structure

Pixel-Guardian/
├── app/
├── assets/
│   └── icons/
├── core/
│   ├── models/
│   └── services/
├── infrastructure/
│   ├── logging/
│   ├── providers/
│   │   └── windows/
│   └── system/
├── ui/
│   ├── navigation/
│   ├── pages/
│   ├── styles/
│   └── widgets/
├── run.py
├── requirements.txt
├── PixelGuardian.spec
├── PixelGuardianInstaller.iss
├── build_exe.bat
└── build_installer.bat

Run From Source

Requirements

Windows 10 or Windows 11

Python 3.12 recommended

Create a virtual environment:

python -m venv .venv

Install dependencies:

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Run Pixel Guardian:

.\.venv\Scripts\python.exe run.py

Build the Windows Application

Build the application with PyInstaller:

.\build_exe.bat

The generated application is placed in:

dist\PixelGuardian\

To create the installer, install Inno Setup 6 and run:

.\build_installer.bat

The installer is generated in:

installer_output\PixelGuardian_Setup_1.0.0.exe

Windows Installer

Pixel Guardian v1.0.0 is packaged as a Windows installer using Inno Setup.

The installer supports:

Per-user installation

Start Menu shortcut

Optional desktop shortcut

Application icon and uninstall entry

Launching Pixel Guardian after installation

The final installer will be available from the repository's GitHub Releases section.

Safety

Pixel Guardian includes system-inspection and cleanup features, so potentially destructive operations are intentionally separated from scanning.

Cleanup results are shown before files are removed.

Administrative elevation is requested only when a supported operation requires it.

The cleaner targets predefined supported cleanup locations rather than arbitrary user files.

Driver functionality is informational and does not automatically install or replace drivers.

Development Approach

Pixel Guardian was developed as an end-to-end product using an AI-assisted development workflow: requirements were broken into individual features, implemented in stages, tested on real Windows systems, and iterated based on actual application behavior.

The application has been built into a standalone Windows executable and tested across multiple PCs.

Demo

A short product demo will be added here after the public v1.0.0 release is published.

Developer

Hamza Omar
Computer Science Student · AI-Assisted Product Builder