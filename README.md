<div align="center">

# Pixel Guardian

### Windows PC monitoring, maintenance, and gaming tools — in one desktop app.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.12-3776AB)
![UI](https://img.shields.io/badge/UI-PySide6%20%2F%20Qt-41CD52)

</div>

<p align="center">
  <img src="./screenshots/01-dashboard.png" alt="Pixel Guardian Dashboard" width="100%">
</p>

## Overview

**Pixel Guardian** is a Windows desktop utility that brings hardware inspection, real-time system monitoring, driver review, safe temporary-file cleanup, disk-health information, and gaming-performance tools into one interface.

The project was built end-to-end as a production-style desktop application, including the application architecture, Windows integrations, packaging, installer, testing, and release workflow.

## Highlights

| Module | What it does |
| --- | --- |
| **Hardware Information** | Displays CPU, GPU, RAM, OS, motherboard, BIOS, storage, and other detected hardware details. |
| **Live Monitor** | Tracks CPU, memory, system drive, running processes, disk activity, network activity, and per-core CPU usage in real time. |
| **Disk Health** | Reviews detected drives, capacity, firmware, operational status, and supported reliability information. |
| **Drivers** | Inspects installed devices and drivers, including status, version, provider, date, signature state, search, and filtering. |
| **Safe Cleaner** | Scans supported temporary-file locations before cleanup and separates standard from administrator-required operations. |
| **Game Lab** | Detects supported Steam/Epic games, checks gaming readiness, and provides FPS estimates using detected CPU/GPU hardware. |

## Product Tour

### Real-time system monitoring
<p align="center">
  <img src="./screenshots/03-live-monitor.png" alt="Pixel Guardian Live Monitor" width="100%">
</p>

### Hardware detection
<p align="center">
  <img src="./screenshots/02-hardware-information.png" alt="Pixel Guardian Hardware Information" width="100%">
</p>

### Gaming performance estimates
<p align="center">
  <img src="./screenshots/04-game-lab.png" alt="Pixel Guardian Game Lab" width="100%">
</p>

### Safe cleanup workflow
<p align="center">
  <img src="./screenshots/06-cleaner.png" alt="Pixel Guardian Cleaner" width="100%">
</p>

### Driver inspection
<p align="center">
  <img src="./screenshots/05-drivers.png" alt="Pixel Guardian Drivers" width="100%">
</p>

## Tech Stack

- **Python 3.12**
- **PySide6 / Qt 6** — desktop UI
- **psutil** — system and performance metrics
- **Windows APIs / Registry / PowerShell integration**
- **PyInstaller** — standalone Windows build
- **Inno Setup 6** — Windows installer

## Architecture

```text
app/              Application bootstrap and startup
core/             Domain models and application services
infrastructure/   Windows providers, logging, paths, and elevation
ui/               PySide6 pages, widgets, navigation, and styles
assets/           Icons and application assets
```

The application uses a layered structure so Windows-specific operations stay separated from UI code and application logic.

## Run From Source

**Requirements:** Windows 10/11 and Python 3.12 recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

## Build

Build the standalone application:

```powershell
.\build_exe.bat
```

Build the installer with Inno Setup 6:

```powershell
.\build_installer.bat
```

Generated installer:

```text
installer_output\PixelGuardian_Setup_1.0.0.exe
```

## Safety

Pixel Guardian separates inspection from destructive operations. Cleanup results are shown before deletion, supported administrator operations request elevation when needed, and driver functionality is informational — it does **not** automatically install or replace drivers.

## Development Approach

Pixel Guardian was developed using an **AI-assisted product-building workflow**: requirements were defined feature by feature, implementation was iterated in stages, behavior was tested on real Windows systems, and the final application was packaged into a standalone executable and installer.

## Demo & Release

**v1.0.0** is the first packaged release. A short product demo and the Windows installer will be linked here as part of the public release.

---

<div align="center">

**Built by Hamza Omar**  
Computer Science Student · AI-Assisted Product Builder

</div>
