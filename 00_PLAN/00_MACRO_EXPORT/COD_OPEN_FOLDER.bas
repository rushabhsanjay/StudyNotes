Attribute VB_Name = "COD_OPEN_FOLDER"
Option Explicit

Sub Open_Current_Folder()

    Dim TopicName As String
    Dim TopicType As String
    Dim ParentPath As String
    Dim TargetPath As String
    Dim FilePath As String
    Dim FileType As String

    StopStuff
    On Error GoTo Fail

    If Not GetSelectedTopic(TopicName, TopicType) Then GoTo Done

    If TopicType <> "FILE" And TopicType <> "FOLDER" Then
        MsgBox "Invalid TOPIC_TYPE for the selected topic:" & vbCrLf & vbCrLf & _
               TopicName & vbCrLf & "TOPIC_TYPE = " & TopicType, vbCritical
        GoTo Done
    End If

    ParentPath = NavigationFolderPath()
    If ParentPath = "" Then GoTo Done

    EnsureFolder ParentPath

    If TopicType = "FOLDER" Then
        TargetPath = ParentPath & TopicName
        EnsureFolder TargetPath
        OpenInExplorer TargetPath
        GoTo Done
    End If

    '---- FILE: open it, or offer to create it ----
    FilePath = FindExistingFile(ParentPath & TopicName)

    If FilePath <> "" Then
        OpenInExplorer FilePath
    Else
        FileType = AskFileType(TopicName)
        If FileType <> "" Then
            CreateOfficeFile ParentPath & TopicName & "." & LCase$(FileType), FileType
        End If
    End If

Done:
    StartStuff
    Exit Sub

Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "Open_Current_Folder"
    Resume Done

End Sub

