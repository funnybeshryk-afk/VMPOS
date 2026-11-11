; VMPOS o'rnatuvchisi (Inno Setup 6).
; Yig'ish:  iscc /DAppVersion=1.0.0 installer\vmpos.iss
; Natija:   dist-installer\VMPOS-Setup-<versiya>.exe
;
; MUHIM: AppId'ni HECH QACHON o'zgartirmang — yangilanish aynan shu
; identifikator bo'yicha eski o'rnatilgan nusxani topib, ustidan yozadi.
;
; Ma'lumotlar (baza, zaxiralar, rasmlar, loglar) %LOCALAPPDATA%\VMPOS da
; va o'rnatuvchi/o'chirgichga umuman TEGMAYDI — dastur fayllari esa
; alohida {localappdata}\Programs\VMPOS ichida. Shu sabab yangilash
; va hatto dasturni o'chirish ham ma'lumotlarni yo'qotmaydi.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{E05B7CBC-F9B4-4140-9597-EFD5A6E69408}
AppName=VMPOS
AppVersion={#AppVersion}
AppPublisher=Vodiy Market
DefaultDirName={localappdata}\Programs\VMPOS
DefaultGroupName=VMPOS
DisableProgramGroupPage=yes
; Administrator huquqi shart emas (foydalanuvchi papkasiga o'rnatiladi) —
; avtomatik yangilash ham so'rovsiz ishlaydi.
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=VMPOS-Setup-{#AppVersion}
SetupIconFile=..\assets\logo.ico
UninstallDisplayIcon={app}\VMPOS.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Ochiq turgan VMPOS.exe'ni yopib, fayllarni almashtiradi.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\VMPOS\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\VMPOS"; Filename: "{app}\VMPOS.exe"
Name: "{autodesktop}\VMPOS"; Filename: "{app}\VMPOS.exe"; Tasks: desktopicon

[Run]
; Oddiy o'rnatishda — "VMPOS'ni ishga tushirish" belgisi.
Filename: "{app}\VMPOS.exe"; Description: "{cm:LaunchProgram,VMPOS}"; Flags: nowait postinstall skipifsilent
; Avtomatik (jim) yangilashda — dastur o'zi qayta ochiladi.
Filename: "{app}\VMPOS.exe"; Flags: nowait; Check: WizardSilent
