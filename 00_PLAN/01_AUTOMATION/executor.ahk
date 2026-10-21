#Requires AutoHotkey v2.0
CoordMode "Mouse", "Screen"

action := A_Args.Length >= 1 ? A_Args[1] : ""
arg2   := A_Args.Length >= 2 ? A_Args[2] : ""
arg3   := A_Args.Length >= 3 ? A_Args[3] : ""

switch action {

    case "activate":
        ; arg2 = WinTitle, e.g. "ahk_exe ChatGPT.exe"
        if !WinExist(arg2) {
            FileAppend "NOT_FOUND", "*"
            ExitApp 1
        }
        WinActivate arg2
        if !WinWaitActive(arg2, , 3) {
            FileAppend "NOT_ACTIVE", "*"
            ExitApp 2
        }
        WinGetPos &x, &y, &w, &h, arg2
        FileAppend x " " y " " w " " h, "*"      ; Python reads this

    case "click":
        ; arg2 = x, arg3 = y (absolute screen pixels)
        MouseMove Integer(arg2), Integer(arg3), 5
        Sleep 100
        Click

    case "paste":
        Send "^v"

    default:
        FileAppend "UNKNOWN_ACTION", "*"
        ExitApp 3
}