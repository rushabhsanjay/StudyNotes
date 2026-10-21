Attribute VB_Name = "COD_OPEN_STUDY_PLAN"
Option Explicit

Sub OPEN_STUDY_PLAN()

    Dim TopicName As String
    Dim TopicType As String
    Dim FolderPath As String
    Dim FilePath As String

    StopStuff
    On Error GoTo Fail

    If Not GetSelectedTopic(TopicName, TopicType) Then GoTo Done

    FolderPath = NavigationFolderPath()
    If FolderPath = "" Then GoTo Done

    FolderPath = FolderPath & TopicName
    FilePath = FolderPath & "\" & STUDY_PLAN_FILE

    If Not FolderExists(FolderPath) Then
        MsgBox "Folder not found:" & vbCrLf & vbCrLf & FolderPath, vbExclamation
        GoTo Done
    End If

    If Not FileExists(FilePath) Then
        MsgBox "Study plan not found:" & vbCrLf & vbCrLf & FilePath, vbExclamation
        GoTo Done
    End If

    OpenInExplorer FilePath

Done:
    StartStuff
    Exit Sub

Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "OPEN_STUDY_PLAN"
    Resume Done

End Sub
