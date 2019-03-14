#define Name      "Росчат"
#define Version   "0.0.1"
#define Publisher "хряНТР"
#define URL       "https://infotek.ru"
#define ExeName   "Росчат.exe"

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

OutputDir=C:\work\roschat-setup
OutputBaseFilename=roschat-setup

Compression=lzma
SolidCompression=yes

;SetupIconFile={app}\roschat5.ico

[Tasks]
;Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";

[Icons]
Name: "{group}\{#Name}"; Filename: "{app}\{#ExeName}"
Name: "{commondesktop}\{#Name}"; IconFilename: "{app}\roschat5.ico"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon


[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
Source: "C:\build\src\roschat\client\dist\dst\roschat-win32-x64\roschat.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\build\src\roschat\client\dist\dst\roschat-win32-x64\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "C:\build\src\roschat\client\dist\img\roschat5.ico"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
