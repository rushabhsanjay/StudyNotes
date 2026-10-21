Attribute VB_Name = "COD_ADM_SHARED"
Option Explicit
'==============================================================
' PATHS AND CONSTANTS  (the only place the root path lives)
'==============================================================
Public Const ROOT_PATH As String = "D:\03_STUDY_FOR_CAREER\"
Public Const STUDY_PLAN_FILE As String = "01_STUDY_INDEX.DOCX"

'==============================================================
' SHARED HELPERS
'==============================================================

Public Function NavigationCell() As Range
    Set NavigationCell = ThisWorkbook.Names("NR_NAVIGATION").RefersToRange.Cells(1, 1)
End Function

Public Function LevelCell() As Range
    Set LevelCell = ThisWorkbook.Names("NR_CURRENT_LEVEL").RefersToRange.Cells(1, 1)
End Function

' Returns the column number of a table header, or 0 if not found
Public Function FindColumn(ByVal tbl As ListObject, ByVal HeaderName As String) As Long
    Dim v As Variant
    v = Application.Match(HeaderName, tbl.HeaderRowRange, 0)
    If IsError(v) Then FindColumn = 0 Else FindColumn = CLng(v)
End Function

' Returns the MasterLevels value; ControlRow = its row in the table (0 if missing)
Public Function GetMasterLevels(ByVal tblMaster As ListObject, _
                                Optional ByRef ControlRow As Long) As Long
    Dim v As Variant
    ControlRow = 0
    v = Application.Match("MasterLevels", tblMaster.ListColumns(2).DataBodyRange, 0)
    If IsError(v) Then Exit Function
    ControlRow = CLng(v)
    GetMasterLevels = CLng(tblMaster.DataBodyRange.Cells(ControlRow, 3).Value)
End Function

' Makes a table have exactly "wanted" data rows (minimum 1)
Private Sub SizeTableRows(ByVal tbl As ListObject, ByVal wanted As Long)
    Dim cur As Long
    If wanted < 1 Then wanted = 1
    If tbl.DataBodyRange Is Nothing Then cur = 0 Else cur = tbl.ListRows.Count

    If cur > wanted Then
        tbl.DataBodyRange.Offset(wanted).Resize(cur - wanted).Delete xlShiftUp
    ElseIf cur < wanted Then
        tbl.Resize tbl.Range.Resize(wanted + 1)
    End If
End Sub

'==============================================================
' LOAD INDEX FOR A NAVIGATION PATH
'
' Navigation = "MasterColumn\Level1\Level2\"
' Shows the topics at level = number of backslashes.
' Sets NR_NAVIGATION and NR_CURRENT_LEVEL only on success.
'==============================================================
Public Function LoadIndex(ByVal Navigation As String) As Boolean

    Dim tblMaster As ListObject
    Dim tblIndex As ListObject
    Dim Data As Variant
    Dim Out() As Variant
    Dim Hits() As Long
    Dim Parts() As String

    Dim Level As Long
    Dim Levels As Long
    Dim IdxCols As Long
    Dim HitCount As Long
    Dim r As Long, c As Long, j As Long
    Dim IsMatch As Boolean

    Set tblMaster = ThisWorkbook.Worksheets("MASTER").ListObjects("MASTER")
    Set tblIndex = ThisWorkbook.Worksheets("INDEX").ListObjects("INDEX")

    If Right$(Navigation, 1) <> "\" Then Navigation = Navigation & "\"
    Parts = Split(Navigation, "\")
    Level = UBound(Parts)                  ' number of backslashes

    Levels = GetMasterLevels(tblMaster)
    If Levels = 0 Then
        MsgBox "MasterLevels control row was not found.", vbCritical
        Exit Function
    End If
    If Level < 1 Or Level > Levels Then
        MsgBox "LEVEL" & Level & " does not exist in MASTER.", vbCritical
        Exit Function
    End If

    ' INDEX column c (c >= 3)  <->  MASTER column c + Levels
    IdxCols = tblIndex.ListColumns.Count
    If IdxCols + Levels > tblMaster.ListColumns.Count Then
        MsgBox "INDEX has more columns than MASTER can supply.", vbCritical
        Exit Function
    End If

    Data = tblMaster.DataBodyRange.Value
    ReDim Hits(1 To UBound(Data, 1))

    ' ---- single pass: find matching rows ----
    For r = 1 To UBound(Data, 1)

        IsMatch = (StrComp(Trim$(CStr(Data(r, 2))), Parts(0), vbTextCompare) = 0)

        If IsMatch Then                        ' path above must match
            For j = 1 To Level - 1
                If StrComp(Trim$(CStr(Data(r, j + 2))), Parts(j), vbTextCompare) <> 0 Then
                    IsMatch = False
                    Exit For
                End If
            Next j
        End If

        If IsMatch Then                        ' must have this level filled
            If Trim$(CStr(Data(r, Level + 2))) = "" Then IsMatch = False
        End If

        If IsMatch Then                        ' and nothing deeper
            For j = Level + 1 To Levels
                If Trim$(CStr(Data(r, j + 2))) <> "" Then
                    IsMatch = False
                    Exit For
                End If
            Next j
        End If

        If IsMatch Then
            HitCount = HitCount + 1
            Hits(HitCount) = r
        End If

    Next r

    ' ---- build output array ----
    If HitCount > 0 Then
        ReDim Out(1 To HitCount, 1 To IdxCols)
        For r = 1 To HitCount
            Out(r, 1) = r
            Out(r, 2) = Data(Hits(r), Level + 2)
            For c = 3 To IdxCols
                Out(r, c) = Data(Hits(r), c + Levels)
            Next c
        Next r
    End If

    ' ---- write INDEX ----
    SizeTableRows tblIndex, HitCount

    If HitCount = 0 Then
        tblIndex.DataBodyRange.ClearContents
    Else
        tblIndex.DataBodyRange.Resize(HitCount, IdxCols).Value = Out
    End If

    NavigationCell.Value = Navigation
    LevelCell.Value = Level
    LoadIndex = True

End Function


' Level of a path = number of backslashes ("A\B\" -> 2)
Public Function PathLevel(ByVal Navigation As String) As Long
    If Navigation = "" Then Exit Function
    If Right$(Navigation, 1) <> "\" Then Navigation = Navigation & "\"
    PathLevel = Len(Navigation) - Len(Replace(Navigation, "\", ""))
End Function

' Full disk path of the current navigation level, ending in "\".
' Returns "" (after a message) if NR_NAVIGATION is empty.
Public Function NavigationFolderPath() As String
    Dim Nav As String
    Nav = CStr(NavigationCell.Value)
    If Nav = "" Then
        MsgBox "NR_NAVIGATION is empty.", vbCritical
        Exit Function
    End If
    If Right$(Nav, 1) <> "\" Then Nav = Nav & "\"
    NavigationFolderPath = ROOT_PATH & Nav
End Function

'==============================================================
' SELECTED INDEX ROW
' Returns the topic name and its TOPIC_TYPE (upper case) for the
' row containing the active cell. Shows a message and returns
' False if the selection is not valid.
'==============================================================
Public Function GetSelectedTopic(ByRef TopicName As String, _
                                 ByRef TopicType As String) As Boolean

    Dim tblIndex As ListObject
    Dim TypeCol As Long
    Dim Pos As Long

    Set tblIndex = ThisWorkbook.Worksheets("INDEX").ListObjects("INDEX")

    If tblIndex.DataBodyRange Is Nothing Then
        MsgBox "INDEX table contains no topics.", vbExclamation
        Exit Function
    End If

    If Not ActiveCell.Worksheet Is tblIndex.Parent Then
        MsgBox "Select a cell inside the INDEX table.", vbExclamation
        Exit Function
    End If

    If Intersect(ActiveCell, tblIndex.DataBodyRange) Is Nothing Then
        MsgBox "Select a cell inside the INDEX table.", vbExclamation
        Exit Function
    End If

    TypeCol = FindColumn(tblIndex, "TOPIC_TYPE")
    If TypeCol = 0 Then
        MsgBox "TOPIC_TYPE column was not found in INDEX.", vbCritical
        Exit Function
    End If

    Pos = ActiveCell.Row - tblIndex.DataBodyRange.Row + 1

    TopicName = Trim$(CStr(tblIndex.DataBodyRange.Cells(Pos, 2).Value))
    If TopicName = "" Then
        MsgBox "The selected row does not contain a topic name.", vbExclamation
        Exit Function
    End If

    TopicType = UCase$(Trim$(CStr(tblIndex.DataBodyRange.Cells(Pos, TypeCol).Value)))
    GetSelectedTopic = True

End Function

'==============================================================
' FILE SYSTEM HELPERS
'==============================================================
Public Function FolderExists(ByVal Path As String) As Boolean
    If Right$(Path, 1) = "\" Then Path = Left$(Path, Len(Path) - 1)
    On Error Resume Next
    FolderExists = ((GetAttr(Path) And vbDirectory) = vbDirectory)
    Err.Clear
End Function

Public Function FileExists(ByVal Path As String) As Boolean
    On Error Resume Next
    FileExists = ((GetAttr(Path) And vbDirectory) = 0)
    Err.Clear
End Function

' Creates a folder and any missing parents
Public Sub EnsureFolder(ByVal Path As String)
    Dim Parts() As String
    Dim Build As String
    Dim i As Long

    If Right$(Path, 1) = "\" Then Path = Left$(Path, Len(Path) - 1)
    Parts = Split(Path, "\")
    Build = Parts(0)                          ' drive, e.g. "D:"

    For i = 1 To UBound(Parts)
        If Parts(i) <> "" Then
            Build = Build & "\" & Parts(i)
            If Not FolderExists(Build) Then MkDir Build
        End If
    Next i
End Sub

Public Sub OpenInExplorer(ByVal Path As String)
    shell "explorer.exe """ & Path & """", vbNormalFocus
End Sub

' Returns the full path of BasePath + .docx/.pptx/.xlsx if one exists, else ""
Public Function FindExistingFile(ByVal BasePath As String) As String
    Dim Ext As Variant
    For Each Ext In Array(".docx", ".pptx", ".xlsx")
        If FileExists(BasePath & Ext) Then
            FindExistingFile = BasePath & Ext
            Exit Function
        End If
    Next Ext
End Function

'==============================================================
' NEW FILE CREATION
'==============================================================
' Shows FRM_CREATE_FILE; returns "DOCX", "PPTX", "XLSX" or "" if cancelled
Public Function AskFileType(ByVal TopicName As String) As String
    FRM_CREATE_FILE.SelectedFileType = ""
    FRM_CREATE_FILE.LBL_TOPIC.Caption = _
        "Topic: " & TopicName & vbCrLf & vbCrLf & "Select file type to create:"
    FRM_CREATE_FILE.Show vbModal
    AskFileType = FRM_CREATE_FILE.SelectedFileType
    Unload FRM_CREATE_FILE
End Function

' Creates an empty Office file at FilePath and opens it
Public Sub CreateOfficeFile(ByVal FilePath As String, ByVal FileType As String)

    Dim App As Object
    Dim Doc As Object

    Select Case FileType
        Case "DOCX"
            Set App = CreateObject("Word.Application")
            Set Doc = App.Documents.Add
            Doc.SaveAs2 FilePath, 16
        Case "PPTX"
            Set App = CreateObject("PowerPoint.Application")
            Set Doc = App.Presentations.Add
            Doc.SaveAs FilePath, 24
        Case "XLSX"
            Set App = CreateObject("Excel.Application")
            Set Doc = App.Workbooks.Add
            Doc.SaveAs FilePath, 51
        Case Else
            Exit Sub
    End Select

    App.Visible = True
    On Error Resume Next
    Doc.Activate                              ' not every Office app supports this
    On Error GoTo 0

End Sub

