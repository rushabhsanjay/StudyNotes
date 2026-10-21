Attribute VB_Name = "COD_OPEN_PARENT"
Option Explicit

Sub OPEN_PARENT_FOLDER()

    Dim ParentPath As String

    StopStuff
    On Error GoTo Fail

    ParentPath = NavigationFolderPath()
    If ParentPath = "" Then GoTo Done

    If Not FolderExists(ParentPath) Then
        MsgBox "Parent folder not found:" & vbCrLf & vbCrLf & ParentPath, vbExclamation
        GoTo Done
    End If

    OpenInExplorer ParentPath

Done:
    StartStuff
    Exit Sub

Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "OPEN_PARENT_FOLDER"
    Resume Done

End Sub
