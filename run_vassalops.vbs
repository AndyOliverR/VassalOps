' VassalOps desktop helper: run bootstrap with a console so errors are visible.
Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\bootstrap_and_run.bat"
WshShell.CurrentDirectory = scriptDir
' Window style 1 = normal (visible) so lay users can see bootstrap progress/errors
WshShell.Run """" & batPath & """", 1, False
