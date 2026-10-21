Attribute VB_Name = "COD_UPDATE_MASTER"
Option Explicit

' Button entry point
Sub UPDATE_MASTER()
    StopStuff
    On Error GoTo Fail
    If SaveIndexToMaster() Then LoadIndex CStr(NavigationCell.Value)   ' reload so folder % is current
Done:
    StartStuff
    Exit Sub
Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "UPDATE_MASTER"
    Resume Done
End Sub

Public Function HasInvalidChars(ByVal s As String) As Boolean
    Dim ch As Variant
    For Each ch In Array("\", "/", ":", "*", "?", """", "<", ">", "|")
        If InStr(s, ch) > 0 Then HasInvalidChars = True: Exit Function
    Next ch
End Function

'==============================================================
' Saves INDEX into MASTER for the path in NR_NAVIGATION.
' Returns False if nothing was saved (validation failed or the
' user declined the deletion prompt) so navigation can abort.
' Does NOT call StopStuff/StartStuff.
'==============================================================
Public Function SaveIndexToMaster() As Boolean

    Dim tblMaster As ListObject
    Dim tblIndex As ListObject
    Dim Parts() As String
    Dim Navigation As String

    Dim Level As Long, Levels As Long, ControlRow As Long
    Dim IdxCols As Long, DataCols As Long

    Dim MData As Variant, IData As Variant
    Dim IndexRows As Object, ExactRow As Object, DeleteTopics As Object
    Dim ScopeTopic() As String
    Dim tmp() As Variant, Blk1() As Variant, Blk2() As Variant, Nums() As Variant

    Dim nM As Long, r As Long, c As Long, j As Long, n As Long
    Dim ir As Long, mr As Long
    Dim NewCount As Long, FirstNew As Long, DelRows As Long
    Dim Topic As String, Msg As String
    Dim InScope As Boolean, IsExact As Boolean
    Dim k As Variant

    Set tblMaster = ThisWorkbook.Worksheets("MASTER").ListObjects("MASTER")
    Set tblIndex = ThisWorkbook.Worksheets("INDEX").ListObjects("INDEX")

    '---- path and structure ----
    Navigation = CStr(NavigationCell.Value)
    If Navigation = "" Then
        MsgBox "NR_NAVIGATION is empty.", vbCritical
        Exit Function
    End If
    If Right$(Navigation, 1) <> "\" Then Navigation = Navigation & "\"
    Parts = Split(Navigation, "\")
    Level = UBound(Parts)

    Levels = GetMasterLevels(tblMaster, ControlRow)
    If ControlRow = 0 Then
        MsgBox "MasterLevels control row was not found.", vbCritical
        Exit Function
    End If
    If Level < 1 Or Level > Levels Then
        MsgBox "LEVEL" & Level & " does not exist in MASTER.", vbCritical
        Exit Function
    End If

    If tblIndex.DataBodyRange Is Nothing Then
        MsgBox "INDEX table contains no data.", vbExclamation
        Exit Function
    End If

    IdxCols = tblIndex.ListColumns.Count
    If IdxCols + Levels > tblMaster.ListColumns.Count Then
        MsgBox "INDEX has more columns than MASTER can supply.", vbCritical
        Exit Function
    End If
    DataCols = IdxCols - 2                    ' INDEX col c (c>=3) <-> MASTER col c + Levels

    '---- read INDEX, check names and duplicates ----
    IData = tblIndex.DataBodyRange.Value
    Set IndexRows = CreateObject("Scripting.Dictionary")
    IndexRows.CompareMode = vbTextCompare

    For r = 1 To UBound(IData, 1)
        Topic = Trim$(CStr(IData(r, 2)))
        If Topic <> "" Then
            If HasInvalidChars(Topic) Then
                MsgBox "Topic name contains a character that is not allowed in folder/file names:" & _
                       vbCrLf & vbCrLf & Topic & vbCrLf & vbCrLf & "No changes were made to MASTER.", vbCritical
                Exit Function
            End If
            If IndexRows.Exists(Topic) Then
                MsgBox "Duplicate topic found in INDEX:" & vbCrLf & vbCrLf & Topic & vbCrLf & vbCrLf & _
                       "Update cancelled. No changes were made to MASTER.", vbCritical
                Exit Function
            End If
            IndexRows.Add Topic, r
        End If
    Next r

    '---- read MASTER once: find rows under this path ----
    MData = tblMaster.DataBodyRange.Value
    nM = UBound(MData, 1)
    ReDim ScopeTopic(1 To nM)
    Set ExactRow = CreateObject("Scripting.Dictionary")
    ExactRow.CompareMode = vbTextCompare

    For r = 1 To nM
        If r <> ControlRow Then
            InScope = (StrComp(Trim$(CStr(MData(r, 2))), Parts(0), vbTextCompare) = 0)

            If InScope Then
                For j = 1 To Level - 1
                    If StrComp(Trim$(CStr(MData(r, j + 2))), Parts(j), vbTextCompare) <> 0 Then
                        InScope = False
                        Exit For
                    End If
                Next j
            End If

            If InScope Then
                Topic = Trim$(CStr(MData(r, Level + 2)))
                If Topic <> "" Then
                    ScopeTopic(r) = Topic          ' this row belongs to Topic (itself or a descendant)

                    IsExact = True                 ' exact = nothing deeper filled
                    For j = Level + 1 To Levels
                        If Trim$(CStr(MData(r, j + 2))) <> "" Then
                            IsExact = False
                            Exit For
                        End If
                    Next j

                    If IsExact Then
                        If Not ExactRow.Exists(Topic) Then ExactRow.Add Topic, r
                    End If
                End If
            End If
        End If
    Next r

    '---- topics removed from INDEX (their descendants go too) ----
    Set DeleteTopics = CreateObject("Scripting.Dictionary")
    DeleteTopics.CompareMode = vbTextCompare

    For Each k In ExactRow.Keys
        If Not IndexRows.Exists(k) Then DeleteTopics.Add k, 0
    Next k

    If DeleteTopics.Count > 0 Then
        For r = 1 To nM
            If ScopeTopic(r) <> "" Then
                If DeleteTopics.Exists(ScopeTopic(r)) Then DelRows = DelRows + 1
            End If
        Next r

        Msg = ""
        n = 0
        For Each k In DeleteTopics.Keys
            n = n + 1
            If n > 10 Then Msg = Msg & "..." & vbCrLf: Exit For
            Msg = Msg & "  - " & k & vbCrLf
        Next k

        If MsgBox(DeleteTopics.Count & " topic(s) are no longer in INDEX and will be DELETED from MASTER:" & _
                  vbCrLf & vbCrLf & Msg & vbCrLf & _
                  "Total rows removed (including sub-topics): " & DelRows & vbCrLf & vbCrLf & _
                  "Continue?", vbYesNo + vbExclamation, "Confirm deletion") <> vbYes Then Exit Function
    End If

    '---- 1) update existing rows ----
    If DataCols > 0 Then ReDim tmp(1 To 1, 1 To DataCols)

    For Each k In IndexRows.Keys
        If ExactRow.Exists(k) Then
            ir = IndexRows(k)
            mr = ExactRow(k)
            With tblMaster.DataBodyRange
                .Cells(mr, Level + 2).Value = k
                If DataCols > 0 Then
                    For c = 1 To DataCols
                        tmp(1, c) = IData(ir, c + 2)
                    Next c
                    .Cells(mr, Levels + 3).Resize(1, DataCols).Value = tmp
                End If
            End With
        End If
    Next k

    '---- 2) delete removed topics, bottom-up ----
    If DeleteTopics.Count > 0 Then
        For r = nM To 1 Step -1
            If ScopeTopic(r) <> "" Then
                If DeleteTopics.Exists(ScopeTopic(r)) Then tblMaster.ListRows(r).Delete
            End If
        Next r
    End If

    '---- 3) add new topics at the end ----
    For Each k In IndexRows.Keys
        If Not ExactRow.Exists(k) Then NewCount = NewCount + 1
    Next k

    If NewCount > 0 Then
        ReDim Blk1(1 To NewCount, 1 To Level + 1)          ' MASTER cols 2 .. Level+2
        If DataCols > 0 Then ReDim Blk2(1 To NewCount, 1 To DataCols)

        n = 0
        For Each k In IndexRows.Keys
            If Not ExactRow.Exists(k) Then
                n = n + 1
                ir = IndexRows(k)
                Blk1(n, 1) = Parts(0)
                For j = 1 To Level - 1
                    Blk1(n, j + 1) = Parts(j)
                Next j
                Blk1(n, Level + 1) = k
                For c = 1 To DataCols
                    Blk2(n, c) = IData(ir, c + 2)
                Next c
            End If
        Next k

        FirstNew = tblMaster.ListRows.Count + 1
        For n = 1 To NewCount
            tblMaster.ListRows.Add
        Next n

        With tblMaster.DataBodyRange
            .Cells(FirstNew, 2).Resize(NewCount, Level + 1).Value = Blk1
            If DataCols > 0 Then .Cells(FirstNew, Levels + 3).Resize(NewCount, DataCols).Value = Blk2
        End With
    End If

    '---- renumber Sr.No in one write ----
    n = tblMaster.ListRows.Count
    ReDim Nums(1 To n, 1 To 1)
    For r = 1 To n
        Nums(r, 1) = r
    Next r
    tblMaster.ListColumns(1).DataBodyRange.Value = Nums

    SaveIndexToMaster = RecalcCompletion()

End Function

