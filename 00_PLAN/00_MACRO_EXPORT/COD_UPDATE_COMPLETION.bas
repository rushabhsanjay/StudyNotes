Attribute VB_Name = "COD_UPDATE_COMPLETION"
Option Explicit

' Button / REFRESH_HARD entry point
Sub UPDATE_MASTER_COMPLETION()
    StopStuff
    On Error GoTo Fail
    RecalcCompletion
Done:
    StartStuff
    Exit Sub
Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "UPDATE_MASTER_COMPLETION"
    Resume Done
End Sub

'==============================================================
' FILE   = manual value (blank = 0)
' FOLDER = average of its direct children, calculated bottom-up
' Rows are grouped by a path key: MasterColumn\Level1\...\LevelN
'==============================================================
Public Function RecalcCompletion() As Boolean

    Dim tbl As ListObject
    Dim Data As Variant
    Dim Result() As Variant
    Dim Depth() As Long
    Dim PathKey() As String
    Dim ParentKey() As String
    Dim Vals() As Double
    Dim Cum() As String
    Dim ChildSum As Object
    Dim ChildCnt As Object

    Dim Levels As Long, ControlRow As Long
    Dim TypeCol As Long, CompCol As Long
    Dim n As Long, r As Long, j As Long, D As Long, MaxDepth As Long
    Dim s As String, TopicType As String

    Set tbl = ThisWorkbook.Worksheets("MASTER").ListObjects("MASTER")

    If tbl.DataBodyRange Is Nothing Then
        MsgBox "MASTER table contains no data.", vbExclamation
        Exit Function
    End If

    Levels = GetMasterLevels(tbl, ControlRow)
    If ControlRow = 0 Then
        MsgBox "MasterLevels control row was not found.", vbCritical
        Exit Function
    End If

    TypeCol = FindColumn(tbl, "TOPIC_TYPE")
    CompCol = FindColumn(tbl, "COMPLETION")
    If TypeCol = 0 Or CompCol = 0 Then
        MsgBox "TOPIC_TYPE or COMPLETION column was not found in MASTER.", vbCritical
        Exit Function
    End If

    Data = tbl.DataBodyRange.Value
    n = UBound(Data, 1)

    ReDim Depth(1 To n)
    ReDim PathKey(1 To n)
    ReDim ParentKey(1 To n)
    ReDim Vals(1 To n)
    ReDim Cum(0 To Levels)

    '---- depth and keys for every row ----
    For r = 1 To n
        If r <> ControlRow Then
            Cum(0) = Trim$(CStr(Data(r, 2)))
            For j = 1 To Levels
                s = Trim$(CStr(Data(r, j + 2)))
                Cum(j) = Cum(j - 1) & "\" & s
                If s <> "" Then Depth(r) = j
            Next j
            If Depth(r) > 0 Then
                PathKey(r) = Cum(Depth(r))
                ParentKey(r) = Cum(Depth(r) - 1)
                If Depth(r) > MaxDepth Then MaxDepth = Depth(r)
            End If
        End If
    Next r

    '---- validate FILE values ----
    For r = 1 To n
        If Depth(r) > 0 Then
            If UCase$(Trim$(CStr(Data(r, TypeCol)))) = "FILE" Then
                s = Trim$(CStr(Data(r, CompCol)))
                If s = "" Then
                    Vals(r) = 0
                ElseIf Not IsNumeric(Data(r, CompCol)) Then
                    MsgBox "Invalid COMPLETION value for FILE:" & vbCrLf & vbCrLf & _
                           PathKey(r) & vbCrLf & "Sheet row: " & (tbl.DataBodyRange.Row + r - 1) & _
                           vbCrLf & "Value: " & s, vbCritical
                    Exit Function
                Else
                    Vals(r) = CDbl(Data(r, CompCol))
                    If Vals(r) < 0 Or Vals(r) > 100 Then
                        MsgBox "FILE completion must be between 0 and 100:" & vbCrLf & vbCrLf & _
                               PathKey(r) & vbCrLf & "Sheet row: " & (tbl.DataBodyRange.Row + r - 1) & _
                               vbCrLf & "Value: " & Vals(r), vbCritical
                        Exit Function
                    End If
                End If
            End If
        End If
    Next r

    '---- roll up from deepest level to level 1 ----
    Set ChildSum = CreateObject("Scripting.Dictionary")
    Set ChildCnt = CreateObject("Scripting.Dictionary")
    ChildSum.CompareMode = vbTextCompare
    ChildCnt.CompareMode = vbTextCompare

    For D = MaxDepth To 1 Step -1
        For r = 1 To n
            If Depth(r) = D Then

                TopicType = UCase$(Trim$(CStr(Data(r, TypeCol))))

                If TopicType = "FOLDER" Then
                    If ChildCnt.Exists(PathKey(r)) Then
                        Vals(r) = ChildSum(PathKey(r)) / ChildCnt(PathKey(r))
                    Else
                        Vals(r) = 0
                    End If
                ElseIf TopicType <> "FILE" Then
                    If IsNumeric(Data(r, CompCol)) Then Vals(r) = CDbl(Data(r, CompCol))
                End If

                If D > 1 Then
                    If ChildCnt.Exists(ParentKey(r)) Then
                        ChildSum(ParentKey(r)) = ChildSum(ParentKey(r)) + Vals(r)
                        ChildCnt(ParentKey(r)) = ChildCnt(ParentKey(r)) + 1
                    Else
                        ChildSum.Add ParentKey(r), Vals(r)
                        ChildCnt.Add ParentKey(r), 1
                    End If
                End If

            End If
        Next r
    Next D

    '---- write back (rows that are not FILE/FOLDER keep their value) ----
    ReDim Result(1 To n, 1 To 1)

    For r = 1 To n
        TopicType = UCase$(Trim$(CStr(Data(r, TypeCol))))
        If Depth(r) > 0 And (TopicType = "FILE" Or TopicType = "FOLDER") Then
            Result(r, 1) = Round(Vals(r), 2)
        Else
            Result(r, 1) = Data(r, CompCol)
        End If
    Next r

    With tbl.ListColumns(CompCol).DataBodyRange
        .Value = Result
        .NumberFormat = "0.00"
    End With

    RecalcCompletion = True

End Function

