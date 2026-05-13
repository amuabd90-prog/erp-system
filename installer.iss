; installer.iss
; Inno Setup script for Amana ERP

#define MyAppName "Amana ERP"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "H&A Solutions"
#define MyAppURL "https://www.yourwebsite.com" ; Change if you have one
#define MyAppExeName "AmanaERP.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId for other applications.
AppId={{F2A6C483-B875-4D39-9A26-347F53A4866F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Amana_ERP_Setup
SetupIconFile=static\icon.ico ; You need to create this icon file
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\AmanaERP\*" ; This is the output from PyInstaller
DestDir: "{app}" ; The folder selected by the user during installation
Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't forget to run build.py first!

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// This section can be used for more advanced scripting,
// like checking for dependencies (e.g., a specific .NET version)
// or for custom uninstallation logic.

