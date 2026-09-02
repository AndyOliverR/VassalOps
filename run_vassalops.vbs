' VassalOps Desktop launcher — no console window.
' Bootstrap errors use a MessageBox + storage\launch.log (see bootstrap_and_run.ps1).
' For a visible debug console, double-click bootstrap_and_run.bat instead.
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
ps1Path = scriptDir & "\bootstrap_and_run.ps1"
WshShell.CurrentDirectory = scriptDir
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1Path & """"
' 0 = hide the launcher window entirely
WshShell.Run cmd, 0, False
