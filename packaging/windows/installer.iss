; Inno Setup script for NexoERP (Windows)
; Gerado automaticamente - revisar antes de usar em produção

#define MyAppName "NexoERP"
#define MyAppPublisher "NexoERP"
#define MyAppURL "https://github.com/ivanmamedio/NexoERP"
#define MyAppExeName "ERP.exe"

[Setup]
AppId={{875EFFD8-4404-4E6E-898F-8CEC9416F7EA}}
AppName={#MyAppName}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=../../LICENSE
OutputDir=../../dist/windows
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
Source: "dist/onedir/*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "dist/onedir/{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{desktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, "&", "&&")}}"; Flags: nowait postinstall skipifsilent
