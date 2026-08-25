#define MyAppName "Pixel Guardian"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Hamza Omar"
#define MyAppExeName "PixelGuardian.exe"

[Setup]
AppId=PixelGuardian.HamzaOmar
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\Pixel Guardian
DefaultGroupName=Pixel Guardian
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=PixelGuardian_Setup_1.0.0
SetupIconFile=assets\icons\pixel_guardian_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\PixelGuardian\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Pixel Guardian"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Pixel Guardian"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Pixel Guardian"; Flags: nowait postinstall skipifsilent
