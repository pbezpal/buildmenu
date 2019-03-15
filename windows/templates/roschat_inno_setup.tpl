#define Name "{{ appname }}"
#define Version   "{{ tag }}"
#define Publisher "OOO ИТСофт"
#define URL       "https://infotek.ru"
#define ExeName   "РосЧат.exe"

{% raw %}
[Setup]
AppId={{7B408B1F-B2FC-48B6-BDDE-32C43D60EB9A}
; AppMutex=/roschat
AppName={#Name}
AppVersion={#Version}
AppPublisher={#Publisher}
AppPublisherURL={#URL}
AppSupportURL={#URL}
AppUpdatesURL={#URL}
; VersionInfoDescription={#Name}
; VersionInfoProductVersion={#Version}
; VersionInfoTextVersion={#Version}
; VersionInfoVersion={#Version}
CloseApplications=force
DefaultDirName={pf}\{#Name}
DefaultGroupName={#Name}
DisableWelcomePage=no
DisableStartupPrompt=yes
DisableDirPage=no
OutputDir=C:\inno_setup_files\
OutputBaseFilename=RosChat setup
Compression=lzma2
; Compression=none
SolidCompression=yes
LicenseFile=license.txt
ShowLanguageDialog=yes
WindowVisible=no
BackColor=clWhite
SetupIconFile=C:\build\src\roschat\client\electron\img\roschat5.ico
; WizardImageFile=C:\build\src\roschat\client\electron\img\roschat_setup11.bmp
; WizardImageStretch=no
; WizardImageBackColor=clBlue
AppCopyright=© ООО "ИТСофт" 2019 г.
FlatComponentsList=no
PrivilegesRequired=admin

[Tasks]
;Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";
Name: "startup"; Description: "Запускать при старте Windows"; GroupDescription: "{cm:AdditionalIcons}"

[Registry]
;current user only
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#Name}"; ValueData: "{app}\{#ExeName}"; Tasks:startup;

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
{% endraw %}
