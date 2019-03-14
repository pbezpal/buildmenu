#define Name      "РосЧат"
#define Version   "0.0.1"
#define Publisher "ИТСофт"
#define URL       "https://infotek.ru"
#define ExeName   "РосЧат.exe"

[Setup]
AppId={{7B408B1F-B2FC-48B6-BDDE-32C43D60EB9A}
AppName={#Name}
AppVersion={#Version}
AppPublisher={#Publisher}
AppPublisherURL={#URL}
AppSupportURL={#URL}
AppUpdatesURL={#URL}

DefaultDirName={pf}\{#Name}
DefaultGroupName={#Name}

OutputDir=C:\inno_setup_files\
OutputBaseFilename=RosChat setup

Compression=lzma
SolidCompression=yes

;SetupIconFile={app}\roschat5.ico

[Tasks]
;Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
Name: "startup"; Description: "Запускать при старте Windows"; GroupDescription: "{cm:AdditionalIcons}"

[Icons]
Name: "{group}\{#Name}"; Filename: "{app}\{#ExeName}"
Name: "{commondesktop}\{#Name}"; IconFilename: "{app}\roschat5.ico"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon


[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "C:\build\src\roschat\client\electron\dst\РосЧат-win32-x64\РосЧат.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\build\src\roschat\client\electron\dst\РосЧат-win32-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\build\src\roschat\client\electron\img\roschat5.ico"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Run]
Filename: {app}\{#ExeName}; Description: {cm:LaunchProgram,{#Name}}; Flags: nowait postinstall skipifsilent

[CustomMessages]
LaunchProgram=Запустить {#Name}