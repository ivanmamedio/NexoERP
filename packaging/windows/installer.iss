; Inno Setup script for NexoERP (Windows)
; Caminhos relativos sao resolvidos em relacao a este script (packaging/windows/).

#define MyAppName "NexoERP"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "NexoERP"
#define MyAppURL "https://github.com/ivanmamedio/NexoERP"
#define MyAppExeName "ERP.exe"

[Setup]
AppId={{875EFFD8-4404-4E6E-898F-8CEC9416F7EA}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
; Instalacao por usuario, sem exigir privilegios administrativos
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=..\..\dist\windows
OutputBaseFilename=NexoERP-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Build onedir do PyInstaller (gerado por release.yml com --distpath dist/windows-latest)
Source: "..\..\dist\windows-latest\ERP\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, "&", "&&")}}"; Flags: nowait postinstall skipifsilent

