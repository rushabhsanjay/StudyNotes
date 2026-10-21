Attribute VB_Name = "COD_BACK"
Option Explicit

Sub TAKE_A_STEP_BACK()

    Dim Navigation As String
    Dim NewNavigation As String
    Dim Parts() As String
    Dim Level As Long
    Dim i As Long

    StopStuff
    On Error GoTo Fail

    Navigation = CStr(NavigationCell.Value)

    If Navigation = "" Then
        MsgBox "NR_NAVIGATION is empty.", vbCritical
        GoTo Done
    End If
    If Right$(Navigation, 1) <> "\" Then Navigation = Navigation & "\"

    Parts = Split(Navigation, "\")
    Level = UBound(Parts)                       ' number of backslashes

    If Level <= 1 Then
        MsgBox "Already at the root level. Cannot move back further.", vbInformation
        GoTo Done
    End If

    '---- save INDEX edits to MASTER before leaving this level ----
    If Not SaveIndexToMaster() Then GoTo Done

    '---- path one level up ----
    For i = 0 To Level - 2
        NewNavigation = NewNavigation & Parts(i) & "\"
    Next i

    '---- load parent level into INDEX ----
    LoadIndex NewNavigation

Done:
    StartStuff
    Exit Sub

Fail:
    MsgBox "Error " & Err.Number & ": " & Err.Description, vbCritical, "TAKE_A_STEP_BACK"
    Resume Done

End Sub
