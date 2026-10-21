Attribute VB_Name = "COD_OPEN_SUBTOPICS"
Option Explicit

Sub OPEN_SUBTOPIC()

    Dim tblMaster As ListObject
    Dim tblIndex As ListObject

    Dim Navigation As String
    Dim NewNavigation As String
    Dim TopicName As String

    Dim NewLevel As Long
    Dim Levels As Long
    Dim ControlRow As Long
    Dim TypeCol As Long
    Dim Pos As Long

    StopStuff
    On Error GoTo Fail

    Set tblMaster = ThisWorkbook.Worksheets("MASTER").ListObjects("MASTER")
    Set tblIndex = ThisWorkbook.Worksheets("INDEX").ListObjects("INDEX")

    '---- validate navigation and selection ----
    Navigation = CStr(NavigationCell.Value)

    If Navigation = "" Then
        MsgBox "NR_NAVIGATION is empty.", vbCritical
        GoTo Done
    End If
    If Right$(Navigation, 1) <> "\" Then Navigation = Navigation & "\"

    If tblIndex.DataBodyRange Is Nothing Then
        MsgBox "INDEX table contains no topics.", vbExclamation
        GoTo Done
    End If

    If Not ActiveCell.Worksheet Is tblIndex.Parent Then
        MsgBox "Select a topic inside the INDEX table.", vbExclamation
        GoTo Done
    End If

    If Intersect(ActiveCell, tblIndex.DataBodyRange) Is Nothing Then
        MsgBox "Select a topic inside the INDEX table.", vbExclamation
        GoTo Done
    End If

    Pos = ActiveCell.Row - tblIndex.DataBodyRange.Row + 1
    TopicName = Trim$(CStr(tblIndex.DataBodyRange.Cells(Pos, 2).Value))

    If TopicName = "" Then
        MsgBox "The selected topic does not contain a topic name.", vbExclamation
        GoTo Done
    End If

    TypeCol = FindColumn(tblIndex, "TOPIC_TYPE")
    If TypeCol = 0 Then
        MsgBox "TOPIC_TYPE column was not found in INDEX.", vbCritical
        GoTo Done
    End If

    If UCase$(Trim$(CStr(tblIndex.DataBodyRange.Cells(Pos, TypeCol).Value))) = "FILE" Then
        MsgBox "The selected topic is marked as FILE." & vbCrLf & vbCrLf & _
               "OPEN_SUBTOPIC will not run for this topic.", vbInformation
        GoTo Done
    End If
    
    '---- save INDEX edits to MASTER before leaving this level ----
    If Not SaveIndexToMaster() Then GoTo Done          ' <-- ADD THIS

    '---- work out the target level ----
    NewNavigation = Navigation & TopicName & "\"
    NewLevel = Len(NewNavigation) - Len(Replace(NewNavigation, "\", ""))

    Levels = GetMasterLevels(tblMaster, ControlRow)
    If ControlRow = 0 Then
        MsgBox "MasterLevels control row was not found.", vbCritical
        GoTo Done
    End If

    '---- offer to create missing LEVEL columns ----
    If NewLevel > Levels Then

        If MsgBox("LEVEL" & NewLevel & " DOES NOT EXIST." & vbCrLf & vbCrLf & _
                  "Current Level : " & (NewLevel - 1) & vbCrLf & _
                  "Master Levels : " & Levels & vbCrLf & vbCrLf & _
                  "Do you want to create LEVEL" & NewLevel & "?", _
                  vbYesNo + vbQuestion, "Create New Level") <> vbYes Then GoTo Done

        Do While Levels < NewLevel
            tblMaster.ListColumns.Add(Levels + 3).Name = "LEVEL" & (Levels + 1)
            Levels = Levels + 1
        Loop

        tblMaster.DataBodyRange.Cells(ControlRow, 3).Value = Levels

    End If

    '---- load children into INDEX ----
    LoadIndex NewNavigation

Done:
    StartStuff
    Exit Sub

Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "OPEN_SUBTOPIC"
    Resume Done

End Sub
