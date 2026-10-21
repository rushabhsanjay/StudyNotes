Attribute VB_Name = "COD_FORMAT_TEXT"
Option Explicit

'============================================================
'  Converts clipboard (ChatGPT / Gemini / Claude output) into
'  a formatted DOCX and opens it.
'  Requires:  Python on PATH  +  python-docx  +  pyperclip
'============================================================
Sub GenerateFormattedDocx()

    Const PY_SCRIPT As String = "D:\00_ADMIN_FILES\02_FORMAT_TEXT_TO_DOCX.PY"
    Const OUT_FILE  As String = "D:\00_ADMIN_FILES\03_FORMATTED_DOCX.docx"

    Dim wdApp As Object, wdDoc As Object, D As Object
    Dim isOpen As Boolean: isOpen = False
    Dim ans As VbMsgBoxResult

    '-- 1. Find a running Word instance (if any) -----------------
    On Error Resume Next
    Set wdApp = GetObject(, "Word.Application")
    On Error GoTo 0

    '-- 2. Is OUT_FILE already open? -----------------------------
    If Not wdApp Is Nothing Then
        For Each D In wdApp.Documents
            If StrComp(D.FullName, OUT_FILE, vbTextCompare) = 0 Then
                Set wdDoc = D
                isOpen = True
                Exit For
            End If
        Next D
    End If

    '-- 3. Ask the user -----------------------------------------
    If isOpen Then
        ans = MsgBox( _
            "'03_FORMATTED_DOCX.docx' is already open in Word." & vbCrLf & vbCrLf & _
            "Continue?" & vbCrLf & _
            "(The open copy will be closed WITHOUT saving.)", _
            vbYesNo + vbQuestion + vbDefaultButton2, _
            "File Already Open")
        If ans = vbNo Then Exit Sub

        On Error Resume Next
        wdDoc.Close SaveChanges:=False
        On Error GoTo 0
        Set wdDoc = Nothing
    End If

    '-- 4. Run Python (hidden console, wait for exit code) ------
    Dim shell As Object: Set shell = CreateObject("WScript.Shell")
    Dim exitCode As Long
    exitCode = shell.Run("cmd /c python """ & PY_SCRIPT & """", 0, True)

    If exitCode <> 0 Then
        MsgBox "Python script failed (exit code " & exitCode & ")." & vbCrLf & vbCrLf & _
               "Check that:" & vbCrLf & _
               "  ? Python is installed and on PATH (try:  python --version)" & vbCrLf & _
               "  ? pyperclip and python-docx are installed" & vbCrLf & _
               "  ? Clipboard actually contains text", _
               vbCritical, "Python Error"
        Exit Sub
    End If

    '-- Python has already opened the file via os.startfile() ---
    Set shell = Nothing
    Set wdApp = Nothing
End Sub

