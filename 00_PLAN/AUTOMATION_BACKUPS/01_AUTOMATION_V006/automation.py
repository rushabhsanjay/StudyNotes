import ctypes
import json
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import mss
import numpy as np
import pyperclip

import queue
import threading
import tkinter as tk

# ---------------- SETTINGS ----------------
# ---- STEP DELAYS (seconds): all response-watching delays are set here ----
SET_WAIT              = 32             # main wait after the send click, before the first check
STILL_RESPONDING_WAIT = SET_WAIT / 4   # re-check delay while the stop button is visible
RECHECK_WAIT          = SET_WAIT / 4   # re-check delay when any other condition is not met yet
MOUSE_MOVE_WAIT       = 0.5              # after moving the mouse to the input bar (no click)
CHECK_DELAY           = 0.8              # pause before EVERY image check
DOWN_ARROW_HOVER_WAIT = 0.6              # mouse resting on the down arrow before clicking it
AFTER_DOWN_CLICK_WAIT = 3              # wait after clicking the down arrow, before re-checking
MEMORY_CHECK_WINDOW   = 3              # both memory images must stay absent this long to carry on as usual
MEMORY_POLL_INTERVAL  = 0.5            # gap between checks inside that window (and while hunting the button)
NEW_CHAT_FIND_TIMEOUT = 9             # once memory-full is seen, how long to look for the Continue button
NEW_CHAT_WAIT         = 9             # after clicking Continue, before checking CONTINUED_OPENED
# --------------------------------------------------------------------------

SCRIPT_DIR     = Path(__file__).resolve().parent
POINTER_FILE   = Path(r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\pointer.json")
PROMPTS_FILE   = str(SCRIPT_DIR / "PROMPTS.txt")
EXTRA_FILE     = str(SCRIPT_DIR / "FIX_PROMPT.txt")

# ---- per-cycle log files (one INDEX_xxxx.TXT per index/cycle) ----
LOG_DIR        = Path(r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\LOG")

AHK_EXE        = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
AHK_SCRIPT     = str(SCRIPT_DIR / "executor.ahk")
CHATGPT_WINDOW = "ahk_exe ChatGPT.exe"

NUM_CYCLES = 3     # how many prompts to process in one run (change later)

# input bar
TEMPLATE_IMG   = str(SCRIPT_DIR / "input_bar.png")
MATCH_THRESHOLD = 0.70
SEARCH_BOTTOM_FRACTION = 0.35
FALLBACK_FROM_BOTTOM = 70

# copy icon (under ChatGPT's last reply)
COPY_ICON_IMG  = str(SCRIPT_DIR / "copy_symbol.png")
COPY_THRESHOLD = 0.80
CONTENT_LEFT_FRACTION = 0.20     # skip the sidebar on the left
GAP_ABOVE_BAR  = 10              # px kept clear above the input bar
CLIPBOARD_WAIT = 3.0             # seconds to wait for the copy to land on the clipboard

# send button
SEND_BUTTON_IMG   = str(SCRIPT_DIR / "SEND_BUTTON.png")
SEND_THRESHOLD    = 0.80
SEND_RETRY_WAIT   = 2.0          # seconds to wait before searching again if not found
SEND_MAX_TRIES    = 2            # first try + one retry after SEND_RETRY_WAIT
SEND_PRE_WAIT     = 0.4          # small pause after paste so the send button can appear

# ---- response watching (after the send click) ----
RESPONDING_STOP_IMG   = str(SCRIPT_DIR / "RESPONDING_STOP.png")        # visible while ChatGPT types
DISABLED_SEND_IMG     = str(SCRIPT_DIR / "DISABLED_SEND_ARROW.png")    # greyed send arrow = idle, empty bar
RESPONDED_VERIFY_IMG  = str(SCRIPT_DIR / "RESPONDED_VERIFICATION.png") # shown when the reply is finished
RESPONDED_DOWN_IMG    = str(SCRIPT_DIR / "RESPONDED_DOWN_ARROW.png")   # scroll-down arrow
NOT_DOWN_OR_SEND_IMG  = str(SCRIPT_DIR / "NOT_DOWN_OR_SEND_ARROW.png") # not used yet
NOT_SCROLLED_IMG      = str(SCRIPT_DIR / "NOT_SCROLLED.png")           # visible while the chat is not scrolled to the bottom
STATE_THRESHOLD       = 0.80     # match threshold for the state images above

# ---- memory full -> continue in a new chat ----
MEMORY_FULL_IMG       = str(SCRIPT_DIR / "MEMORY_FULL_INFO.png")   # "memory / conversation full" notice
CONTINUE_NEW_CHAT_IMG = str(SCRIPT_DIR / "COTINUE_NEW_CHAT.png")   # the Continue-in-new-chat button
CONTINUED_OPENED_IMG  = str(SCRIPT_DIR / "CONTINUED_OPENED.png")   # visible once the new chat has opened
NEW_CHAT_THRESHOLD    = 0.80

MAX_CYCLE_SECONDS     = 420      # one cycle's time limit (10 minutes)

# ---- timeout recovery (time limit hit while waiting for ChatGPT's reply) ----
MAX_RESEND_RETRIES    = 3        # how many times one cycle may stop/resend before it terminates
RECOVERY_MOUSE_WAIT   = 1        # seconds after moving the mouse to the input bar, before checking
RECOVERY_AFTER_STOP_WAIT = 1.0   # settle time after clicking the stop button

# DOCX generation (Python version of the VBA GenerateFormattedDocxDirect)
FILE_CHECK_FILE   = str(SCRIPT_DIR / "FILE_CHECK.TXT")   # lines: |INDEX|PATH|FILENAME.DOCX|
FILE_CHECK_OFFSET = -1           # row checked = pointer index + this (-1 = previous index)
STOP_IF_NOT_LISTED = True        # True: no matching row in FILE_CHECK.TXT -> stop, paste nothing
PY_SCRIPT      = r"D:\00_ADMIN_FILES\02_FORMAT_TEXT_TO_DOCX.PY"
ARGS_FILE      = r"D:\00_ADMIN_FILES\_py_args.txt"
PYTHON_EXE     = "python"
DOCX_TIMEOUT   = 120             # seconds; the script normally needs ~3
DOCX_SETTLE    = 0.5             # extra pause after the DOCX script finishes

# verification
TAIL_SENTENCES = 4               # how many sentences/lines from the END of the reply to check
PATH_SEGMENTS_TO_CHECK = 3       # last N path segments (ignores the long root prefix)
MATCH_MIN      = 0.90            # both path score and label score must reach this
COPIED_DEBUG_FILE = str(SCRIPT_DIR / "copied_debug.txt")   # copied reply is saved here every run

JOINER = "\n\n"
SENTINEL = "__WAITING_FOR_CHATGPT_COPY__"
# ------------------------------------------

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

MSS = getattr(mss, "MSS", None) or mss.mss


# ---------- always-on-top live terminal window (left side, portrait) ----------
UI_Q = queue.Queue()
WIN_W_FRAC, WIN_H_FRAC = 0.15, 0.70


class LiveWindow(threading.Thread):
    """Tk lives entirely in this thread; everything reaches it through UI_Q."""

    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        root = tk.Tk()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = int(sw * WIN_W_FRAC), int(sh * WIN_H_FRAC)
        X_OFFSET = int(sw * 0.02)    # shift right: 2% of screen width (try 0.01 to 0.05)
        root.geometry(f"{w}x{h}+{X_OFFSET}+{(sh - h) // 2}")
        root.overrideredirect(True)              # no title bar / close button
        root.attributes("-topmost", True)
        txt = tk.Text(root, bg="black", fg="#00ff66", font=("Consolas", 8),
                      wrap="word", bd=0, state="disabled")
        txt.pack(fill="both", expand=True)

        def poll():
            try:
                while True:
                    item = UI_Q.get_nowait()
                    if isinstance(item, tuple):          # ("end", is_error)
                        if item[1]:
                            root.configure(bg="red")
                            txt.configure(bg="red", fg="white")
                            root.after(2000, root.destroy)   # hold red for 2 s
                        else:
                            root.destroy()
                        return
                    txt.configure(state="normal")
                    txt.insert("end", item)
                    if int(txt.index("end-1c").split(".")[0]) > 2000:
                        txt.delete("1.0", "500.0")
                    txt.see("end")
                    txt.configure(state="disabled")
            except queue.Empty:
                pass
            root.lift()
            root.attributes("-topmost", True)            # stay above other apps
            root.after(100, poll)

        poll()
        root.mainloop()


LIVE = LiveWindow()


def close_live_window(is_error: bool):
    """Red for 2 s on error, then close. (Later: the 'final checks + paste' script goes here.)"""
    UI_Q.put(("end", is_error))
    LIVE.join(timeout=6)


# ---------- per-cycle logging (terminal output is mirrored into LOG\INDEX_xxxx.TXT) ----------
_LOG = {"file": None, "bol": True, "path": None}   # bol = "at beginning of line"


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _log_write(s: str):
    """Write text to the current cycle log (timestamp at the start of every line).
    Never raises: a logging problem must not affect the automation."""
    f = _LOG["file"]
    if f is None or not s:
        return
    try:
        out = []
        for part in s.splitlines(keepends=True):
            if _LOG["bol"]:
                out.append(f"[{_ts()}] ")
            out.append(part)
            _LOG["bol"] = part.endswith("\n")
        f.write("".join(out))
        f.flush()
    except Exception:
        pass


class _Tee:
    """Passes everything through to the real stream AND copies it into the cycle log."""

    def __init__(self, stream):
        self._stream = stream

    def write(self, s):
        n = len(s) if isinstance(s, str) else 0
        if self._stream is not None:
            try:
                self._stream.write(s)
            except Exception:
                pass
        if isinstance(s, str):
            _log_write(s)
            UI_Q.put(s) 
        return n

    def flush(self):
        if self._stream is not None:
            try:
                self._stream.flush()
            except Exception:
                pass

    def __getattr__(self, name):          # encoding, isatty, fileno, ...
        return getattr(self._stream, name)


sys.stdout = _Tee(sys.stdout)
sys.stderr = _Tee(sys.stderr)


def stop_cycle_log(note: str = ""):
    """Close the current cycle log (if any), optionally writing a final line first."""
    f = _LOG["file"]
    if f is None:
        return
    try:
        if note:
            if not _LOG["bol"]:
                _log_write("\n")
            _log_write(note + "\n")
        f.close()
    except Exception:
        pass
    _LOG["file"] = None
    _LOG["bol"] = True


def start_cycle_log(index: int, cycle_no: int):
    """Open LOG\\INDEX_xxxx.TXT for this cycle (appends if it already exists)."""
    stop_cycle_log("Cycle log closed (next cycle starting).")
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = LOG_DIR / f"INDEX_{index:04d}.TXT"
        _LOG["file"] = open(path, "a", encoding="utf-8", errors="replace")
        _LOG["bol"] = True
        _LOG["path"] = path
        _log_write("=" * 70 + "\n")
        _log_write(f"LOG FOR INDEX [{index:04d}]  |  cycle {cycle_no} of {NUM_CYCLES}  |  "
                   f"started {_ts()}\n")
        _log_write(f"Script: {Path(__file__).resolve()}\n")
        _log_write(f"Log file: {path}\n")
        _log_write("=" * 70 + "\n")
    except Exception as e:
        _LOG["file"] = None
        _LOG["bol"] = True
        print(f"WARNING: could not open log file for index {index:04d}: {e}")


class CycleTimeout(Exception):
    """Raised when one cycle runs longer than MAX_CYCLE_SECONDS."""


def sleep_checked(seconds: float, deadline: float):
    """Sleep, but never past the cycle deadline (raises CycleTimeout instead)."""
    remaining = deadline - time.time()
    if remaining <= 0:
        raise CycleTimeout()
    if seconds >= remaining:
        time.sleep(remaining)
        raise CycleTimeout()
    time.sleep(seconds)


# ---------- pointer + prompts ----------
def load_pointer() -> int:
    data = json.loads(POINTER_FILE.read_text(encoding="utf-8"))
    return int(data["index"])


def save_pointer(new_index: int):
    """Write the new index back, keeping any other keys in pointer.json."""
    try:
        data = json.loads(POINTER_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    data["index"] = new_index
    POINTER_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_prompt(index: int) -> str:
    """Return only the prompt text of block [index] (no number, no separator)."""
    text = Path(PROMPTS_FILE).read_text(encoding="utf-8-sig")
    for block in re.split(r"\r?\n-{20,}\r?\n", text):
        m = re.match(rf"\s*\[{index:04d}\]\r?\n(.*)", block.strip(), re.DOTALL)
        if m:
            return m.group(1).strip()
    raise ValueError(f"Prompt [{index:04d}] not found in {PROMPTS_FILE}")


def prompt_exists(index: int) -> bool:
    """True if PROMPTS.txt has a block [index]."""
    try:
        get_prompt(index)
        return True
    except ValueError:
        return False


def expected_topic(prompt: str):
    """From line 1 'YES THE NEXT IS <path>\\<topic> - <desc>' return (full_path, label)."""
    line1 = prompt.splitlines()[0]
    full = re.sub(r"^\s*YES THE NEXT IS\s+", "", line1, flags=re.I).strip()
    # drop the trailing " - description": the reply's NEXT TOPIC line only shows the path
    full = re.sub(r"\s+-\s+[^\\]*$", "", full).strip()
    label = full.rsplit("\\", 1)[-1].strip()
    return full, label


def build_clipboard_text(prompt: str) -> str:
    extra = Path(EXTRA_FILE).read_text(encoding="utf-8-sig").strip()
    return prompt + JOINER + extra


# ---------- AutoHotkey bridge ----------
def ahk(*args) -> str:
    r = subprocess.run([AHK_EXE, AHK_SCRIPT, *map(str, args)],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0:
        raise RuntimeError(f"AHK failed ({out or r.stderr.strip()})")
    return out


def activate_window():
    """Bring ChatGPT forward and return its (x, y, w, h)."""
    return tuple(map(int, ahk("activate", CHATGPT_WINDOW).split()))


def move_mouse(x, y):
    """Move the real cursor to screen (x, y) WITHOUT clicking."""
    ctypes.windll.user32.SetCursorPos(int(x), int(y))


# ---------- vision ----------
def find_image(img_path, threshold, win, label, bottom_fraction=None):
    """Template-match img_path inside the ChatGPT window (or its bottom part).
    Returns the (x, y) screen centre of the best match, or None."""
    if not Path(img_path).exists():
        print(f"Missing image: {img_path}")
        return None

    win_x, win_y, win_w, win_h = win
    if bottom_fraction:
        top = win_y + int(win_h * (1 - bottom_fraction))
    else:
        top = win_y
    region = {"left": win_x, "top": top, "width": win_w, "height": win_y + win_h - top}

    tpl = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if tpl is None:
        print(f"Could not read image: {img_path}")
        return None
    with MSS() as sct:
        shot = np.array(sct.grab(region))
    gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
    if gray.shape[0] < tpl.shape[0] or gray.shape[1] < tpl.shape[1]:
        return None

    res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    found = score >= threshold
    print(f"  [{label}] score {score:.2f} -> {'PRESENT' if found else 'absent'}")
    if not found:
        return None
    return (region["left"] + loc[0] + tpl.shape[1] // 2,
            region["top"] + loc[1] + tpl.shape[0] // 2)


def find_input_bar(win_x, win_y, win_w, win_h):
    """Return (x, y) screen coords of the input bar. Template match first, fallback second."""
    top = win_y + int(win_h * (1 - SEARCH_BOTTOM_FRACTION))
    region = {"left": win_x, "top": top, "width": win_w, "height": win_y + win_h - top}

    if Path(TEMPLATE_IMG).exists():
        tpl = cv2.imread(TEMPLATE_IMG, cv2.IMREAD_GRAYSCALE)
        with MSS() as sct:
            shot = np.array(sct.grab(region))
        gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
        if gray.shape[0] >= tpl.shape[0] and gray.shape[1] >= tpl.shape[1]:
            res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)
            print(f"Input bar match score: {score:.2f}")
            if score >= MATCH_THRESHOLD:
                return (region["left"] + loc[0] + tpl.shape[1] // 2,
                        region["top"] + loc[1] + tpl.shape[0] // 2)
        print("Input bar template not matched - using fallback position.")
    else:
        print("No input bar template - using fallback position.")

    return win_x + win_w // 2, win_y + win_h - FALLBACK_FROM_BOTTOM


def find_copy_icon(win_x, win_y, win_w, bar_y):
    """Find the LOWEST copy icon in the chat area (= the last reply's). Returns (x, y) or None."""
    if not Path(COPY_ICON_IMG).exists():
        print(f"Missing copy icon image: {COPY_ICON_IMG}")
        return None

    left = win_x + int(win_w * CONTENT_LEFT_FRACTION)
    region = {"left": left, "top": win_y,
              "width": win_x + win_w - left,
              "height": max(50, bar_y - GAP_ABOVE_BAR - win_y)}

    tpl = cv2.imread(COPY_ICON_IMG, cv2.IMREAD_GRAYSCALE)
    with MSS() as sct:
        shot = np.array(sct.grab(region))
    gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
    if gray.shape[0] < tpl.shape[0] or gray.shape[1] < tpl.shape[1]:
        return None

    res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(res >= COPY_THRESHOLD)
    if len(ys) == 0:
        print(f"Copy icon not found (best score {res.max():.2f}, needs {COPY_THRESHOLD}).")
        return None

    y, x = max(zip(ys, xs), key=lambda p: (p[0], res[p[0], p[1]]))   # lowest on screen
    print(f"Copy icon match score: {res[y, x]:.2f}")
    return (region["left"] + int(x) + tpl.shape[1] // 2,
            region["top"] + int(y) + tpl.shape[0] // 2)


def click_send_button(win, deadline) -> bool:
    """Locate the send button (retrying after a wait) and click it."""
    for attempt in range(1, SEND_MAX_TRIES + 1):
        pos = find_image(SEND_BUTTON_IMG, SEND_THRESHOLD, win, "send button",
                         bottom_fraction=SEARCH_BOTTOM_FRACTION)
        if pos is not None:
            print(f"Clicking send button at {pos}")
            ahk("click", pos[0], pos[1])
            return True
        if attempt < SEND_MAX_TRIES:
            print(f"Send button not found - waiting {SEND_RETRY_WAIT:.0f}s and trying again.")
            sleep_checked(SEND_RETRY_WAIT, deadline)
            win = activate_window()
    print("Send button never matched. Prompt is pasted but NOT sent.")
    return False


# ---------- copy ChatGPT's reply ----------
def copy_chatgpt_reply(win_x, win_y, win_w, bar_y):
    """Click the copy icon and return the copied text (None if it failed)."""
    pos = find_copy_icon(win_x, win_y, win_w, bar_y)
    if pos is None:
        return None

    pyperclip.copy(SENTINEL)                       # so we can tell when the copy really happened
    print(f"Clicking copy icon at {pos}")
    ahk("click", pos[0], pos[1])

    deadline = time.time() + CLIPBOARD_WAIT
    while time.time() < deadline:
        txt = pyperclip.paste()
        if txt and txt != SENTINEL:
            return txt
        time.sleep(0.1)
    return None


# ---------- FILE_CHECK.TXT lookup ----------
def lookup_file_check(index: int):
    """Find the row |INDEX|PATH|FILENAME.DOCX| for `index` in FILE_CHECK.TXT.
    Returns (parent_folder_with_trailing_backslash, file_stem, full_docx_path) or None."""
    fc = Path(FILE_CHECK_FILE)
    if not fc.exists():
        print(f"Missing {FILE_CHECK_FILE}")
        return None

    for raw in fc.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line:
            continue
        line = line.strip("|")
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3 or not parts[0].isdigit():
            continue                                  # header or malformed line
        if int(parts[0]) != index:
            continue

        folder, fname = parts[1], parts[2]
        if not folder or not fname:
            print(f"FILE_CHECK.TXT row {index} has an empty path or file name.")
            return None

        parent = folder.rstrip("\\/") + "\\"          # trailing "\" like the VBA ParentPath
        if not re.match(r"^[A-Za-z]:\\", parent):
            print(f"FILE_CHECK.TXT row {index}: path is not absolute "
                  f"(needs a drive letter like D:\\): {parent}")
            return None
        stem = fname[:-5] if fname.lower().endswith(".docx") else fname
        return parent, stem, str(Path(parent) / f"{stem}.docx")

    print(f"Index {index} not found in {FILE_CHECK_FILE}.")
    return None


# ---------- DOCX generation (Python version of the VBA macro) ----------
def ensure_docx(index: int) -> bool:
    """Check the DOCX listed for (index + FILE_CHECK_OFFSET) in FILE_CHECK.TXT.
    Exists -> skip. Missing -> run the formatter (it reads the reply from the clipboard).
    Returns False only if generation was needed and failed (or the row is missing and
    STOP_IF_NOT_LISTED is True)."""
    check_index = index + FILE_CHECK_OFFSET
    row = lookup_file_check(check_index)
    if row is None:
        if STOP_IF_NOT_LISTED:
            return False
        print("DOCX step skipped (not listed).")
        return True

    parent, stem, final_path = row
    final = Path(final_path)
    print(f"DOCX check for index {check_index}: {final_path}")

    if final.exists():
        print("DOCX already exists, skipping generation.")
        return True

    print("DOCX not found - generating.")
    try:
        Path(parent).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Could not create folder {parent}: {e}")
        return False

    # same hand-off as the VBA: line 1 = destination folder, line 2 = file stem
    Path(ARGS_FILE).write_text(f"{parent}\n{stem}\n", encoding="utf-8")

    try:
        r = subprocess.run([PYTHON_EXE, PY_SCRIPT], capture_output=True, text=True,
                           timeout=DOCX_TIMEOUT,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        print(f"DOCX script timed out after {DOCX_TIMEOUT}s.")
        return False
    finally:
        try:
            Path(ARGS_FILE).unlink()          # clean up if the formatter couldn't
        except OSError:
            pass

    if r.returncode != 0:
        print(f"DOCX script failed (exit code {r.returncode}).")
        print((r.stderr or r.stdout).strip()[-800:])
        print("Check: python on PATH, pyperclip, python-docx, latex2mathml, lxml (and markdown "
              "for the HTML companion), and that the clipboard holds text.")
        return False

    if not final.exists():
        print(f"DOCX script finished but the file was not created: {final_path}")
        return False

    time.sleep(DOCX_SETTLE)
    print("DOCX created.")
    return True


# ---------- verification (plain text matching, no model) ----------
def norm(s: str) -> str:
    """Lowercase and keep only letters/digits, so markdown, spaces and punctuation don't matter."""
    return re.sub(r"[\W_]+", "", s.lower())


def last_sentences(text: str, n: int) -> str:
    chunks = [c.strip() for c in re.split(r"(?<=[.!?])\s+|[\r\n]+", text) if c.strip()]
    return " ".join(chunks[-n:])


def match_score(expected: str, tail: str) -> float:
    """1.0 = found exactly. Otherwise best sliding-window fuzzy ratio, with a strict digit check."""
    e, t = norm(expected), norm(tail)
    if not e or not t:
        return 0.0
    if e in t:
        return 1.0

    w = min(len(e), len(t))
    sm = SequenceMatcher(None, autojunk=False)
    sm.set_seq2(e)
    best, start = 0.0, 0
    for i in range(0, len(t) - w + 1):
        sm.set_seq1(t[i:i + w])
        r = sm.ratio()
        if r > best:
            best, start = r, i

    # numbers must match exactly (03 vs 04 would otherwise score ~0.92)
    pad = t[max(0, start - 3): start + w + 3]
    if "".join(re.findall(r"\d+", e)) not in "".join(re.findall(r"\d+", pad)):
        return min(best, 0.5)
    return best


def verify(copied: str, full_path: str, label: str):
    tail = last_sentences(copied, TAIL_SENTENCES)
    path_part = "\\".join(full_path.split("\\")[-PATH_SEGMENTS_TO_CHECK:])
    path_score = match_score(path_part, tail)
    label_score = match_score(label, tail)
    print(f"Tail checked: ...{tail[-300:]}")
    print(f"Path score: {path_score:.2f}   Label score: {label_score:.2f}   (need {MATCH_MIN} each)")
    return path_score >= MATCH_MIN and label_score >= MATCH_MIN


# ---------- wait for ChatGPT's response ----------
def wait_for_response(deadline: float) -> bool:
    """Called right after the send click. Returns True only when ALL of these hold in the
    same pass: stop button absent, down arrow absent, NOT_SCROLLED absent, disabled send
    arrow present, and responded verification present (checked last).
    Raises CycleTimeout if the cycle deadline passes."""

    def locate(img, label):
        sleep_checked(CHECK_DELAY, deadline)          # settle delay before EVERY check
        return find_image(img, STATE_THRESHOLD, win, label)

    def present(img, label):
        return locate(img, label) is not None

    print(f"Waiting {SET_WAIT:.0f}s for ChatGPT to respond...")
    sleep_checked(SET_WAIT, deadline)

    while True:
        win = activate_window()
        print("Checking response state:")

        # 0. park the mouse on the input bar (no click) and let the screen settle
        bar = find_input_bar(*win)
        print(f"Moving mouse to input bar {bar} (no click), waiting {MOUSE_MOVE_WAIT}s.")
        move_mouse(*bar)
        sleep_checked(MOUSE_MOVE_WAIT, deadline)

        # 1. still typing -> wait and look again
        if present(RESPONDING_STOP_IMG, "responding stop"):
            print(f"Still responding - waiting {STILL_RESPONDING_WAIT:.0f}s.")
            sleep_checked(STILL_RESPONDING_WAIT, deadline)
            continue

        # 2. scroll-down arrow visible -> hover, click, wait, then re-check everything
        pos = locate(RESPONDED_DOWN_IMG, "responded down arrow")
        if pos is not None:
            print(f"Down arrow present - moving mouse to {pos}, waiting {DOWN_ARROW_HOVER_WAIT}s.")
            move_mouse(*pos)
            sleep_checked(DOWN_ARROW_HOVER_WAIT, deadline)
            print("Clicking down arrow.")
            ahk("click", pos[0], pos[1])
            print(f"Waiting {AFTER_DOWN_CLICK_WAIT}s after the click, then re-checking.")
            sleep_checked(AFTER_DOWN_CLICK_WAIT, deadline)
            continue

        # 3. chat still not scrolled to the bottom (and no down arrow to fix it) -> retry
        if present(NOT_SCROLLED_IMG, "not scrolled"):
            print(f"NOT_SCROLLED is visible but the down arrow is absent - waiting {RECHECK_WAIT:.0f}s.")
            sleep_checked(RECHECK_WAIT, deadline)
            continue

        # 4. greyed send arrow = ChatGPT is idle
        if not present(DISABLED_SEND_IMG, "disabled send arrow"):
            print(f"Disabled send arrow not visible - waiting {RECHECK_WAIT:.0f}s.")
            sleep_checked(RECHECK_WAIT, deadline)
            continue

        # 5. finally, the reply-finished marker
        if present(RESPONDED_VERIFY_IMG, "responded verification"):
            print("Response complete.")
            return True

        print(f"Responded verification not visible - waiting {RECHECK_WAIT:.0f}s.")
        sleep_checked(RECHECK_WAIT, deadline)


# ---------- timeout recovery: stop (if needed) -> paste again -> send again ----------
def recover_and_resend(index: int, deadline: float) -> bool:
    """Used when the cycle time limit ran out while waiting for ChatGPT's reply.
    1. Move the mouse to the input bar, wait RECOVERY_MOUSE_WAIT seconds.
    2. RESPONDING_STOP present -> click it.
       Otherwise DISABLED_SEND_ARROW present -> nothing to stop.
       Neither present -> give up (returns False).
    3. Go to the input bar, paste the prompt again and click send.
    Returns True if the prompt was sent again, else False."""
    win = activate_window()
    bar = find_input_bar(*win)
    print(f"RECOVERY: moving mouse to input bar {bar} (no click), waiting {RECOVERY_MOUSE_WAIT}s.")
    move_mouse(*bar)
    sleep_checked(RECOVERY_MOUSE_WAIT, deadline)

    stop_pos = find_image(RESPONDING_STOP_IMG, STATE_THRESHOLD, win, "recovery: responding stop")
    if stop_pos is not None:
        print(f"RECOVERY: stop button present - clicking it at {stop_pos}.")
        ahk("click", stop_pos[0], stop_pos[1])
        sleep_checked(RECOVERY_AFTER_STOP_WAIT, deadline)
    else:
        if find_image(DISABLED_SEND_IMG, STATE_THRESHOLD, win,
                      "recovery: disabled send arrow") is None:
            print("RECOVERY FAILED: neither the stop button nor the disabled send arrow is visible.")
            return False
        print("RECOVERY: stop button absent, disabled send arrow present - resending.")

    # back to the input bar -> paste the prompt again -> send again
    win = activate_window()
    bx, by = find_input_bar(*win)
    prompt = get_prompt(index)
    pyperclip.copy(build_clipboard_text(prompt))
    print(f"RECOVERY: clipboard set for prompt [{index:04d}]. Clicking input bar at ({bx}, {by})")
    ahk("click", bx, by)
    sleep_checked(0.3, deadline)
    ahk("paste")

    sleep_checked(SEND_PRE_WAIT, deadline)
    if not click_send_button(win, deadline):
        print("RECOVERY FAILED: could not click the send button.")
        return False
    print("RECOVERY: prompt sent again.")
    return True


# ---------- memory full -> continue in a new chat ----------
def handle_new_chat(deadline: float) -> bool:
    """Look for the memory-full notice or the Continue-in-new-chat button.
    - Neither shows up for MEMORY_CHECK_WINDOW seconds -> True (carry on as usual).
    - Either shows up -> click the Continue button, wait NEW_CHAT_WAIT, then require
      CONTINUED_OPENED to be visible -> True. Anything else -> False (stop, nothing pasted)."""
    win = activate_window()
    print(f"Checking for memory-full / continue-new-chat for {MEMORY_CHECK_WINDOW}s...")

    start = time.time()
    triggered = False
    while time.time() - start < MEMORY_CHECK_WINDOW:
        if (find_image(MEMORY_FULL_IMG, NEW_CHAT_THRESHOLD, win, "memory full info") is not None
                or find_image(CONTINUE_NEW_CHAT_IMG, NEW_CHAT_THRESHOLD, win,
                              "continue new chat") is not None):
            triggered = True
            break
        sleep_checked(MEMORY_POLL_INTERVAL, deadline)

    if not triggered:
        print("Neither memory-full nor continue-new-chat appeared - carrying on as usual.")
        return True

    print("Memory-full detected - looking for the Continue button.")
    find_start = time.time()
    while True:
        pos = find_image(CONTINUE_NEW_CHAT_IMG, NEW_CHAT_THRESHOLD, win, "continue new chat")
        if pos is not None:
            break
        if time.time() - find_start >= NEW_CHAT_FIND_TIMEOUT:
            print(f"Stopped: Continue button not found within {NEW_CHAT_FIND_TIMEOUT}s. Nothing pasted.")
            return False
        sleep_checked(MEMORY_POLL_INTERVAL, deadline)
        win = activate_window()

    print(f"Clicking continue-in-new-chat at {pos}")
    ahk("click", pos[0], pos[1])
    print(f"Waiting {NEW_CHAT_WAIT}s for the new chat to open...")
    sleep_checked(NEW_CHAT_WAIT, deadline)

    win = activate_window()
    if find_image(CONTINUED_OPENED_IMG, NEW_CHAT_THRESHOLD, win, "continued opened") is None:
        print("Stopped: the new chat did not open (CONTINUED_OPENED not found). Nothing pasted.")
        return False
    print("New chat opened.")
    return True


# ---------- one full cycle ----------
def step3(deadline: float):
    """Copy -> DOCX -> verify -> memory-full check -> paste -> send.
    Returns (index, window) on success, else None."""
    # 1. pointer -> prompt + expected topic
    index = load_pointer()
    prompt = get_prompt(index)
    full_path, label = expected_topic(prompt)
    print(f"Pointer: [{index:04d}]  Expected: {full_path}")

    # 2. bring ChatGPT forward, locate the input bar
    win = activate_window()
    wx, wy, ww, wh = win
    print(f"ChatGPT window: x={wx} y={wy} w={ww} h={wh}")
    sleep_checked(0.5, deadline)
    bx, by = find_input_bar(wx, wy, ww, wh)

    # 3. copy ChatGPT's last reply via its copy icon
    copied = copy_chatgpt_reply(wx, wy, ww, by)
    if copied is None:
        print("Stopped: could not copy the reply. Nothing pasted.")
        return None
    Path(COPIED_DEBUG_FILE).write_text(copied, encoding="utf-8")
    print(f"Copied {len(copied)} characters.")

    # 4. DOCX: look up index-1 in FILE_CHECK.TXT; skip if the file exists, else generate.
    #    (The clipboard still holds the copied reply, which the formatter reads.)
    if not ensure_docx(index):
        print("Stopped: DOCX check/generation failed. Nothing pasted.")
        return None

    # 5. verify the end of the reply against the pointer's topic
    if not verify(copied, full_path, label):
        print("Stopped: on-screen topic does not match the pointer. Nothing pasted.")
        return None
    print("MATCH confirmed.")

    # 6. memory full? -> Continue in a new chat first (input bar is NOT looked for yet)
    if not handle_new_chat(deadline):
        return None

    # 7. now look for the input bar (it may be in a new chat), then clipboard -> paste
    win = activate_window()
    wx, wy, ww, wh = win
    bx, by = find_input_bar(wx, wy, ww, wh)
    pyperclip.copy(build_clipboard_text(prompt))
    print(f"Clipboard set for prompt [{index:04d}]. Clicking input bar at ({bx}, {by})")
    ahk("click", bx, by)
    sleep_checked(0.3, deadline)
    ahk("paste")

    # 8. click the send button (wait 2s and retry once if it isn't visible yet)
    sleep_checked(SEND_PRE_WAIT, deadline)
    if not click_send_button(win, deadline):
        return None
    return index, win


def _run() -> int:
    for cycle_no in range(1, NUM_CYCLES + 1):
        # stop cleanly if the pointer is already past the last entry
        if not prompt_exists(load_pointer()):
            print("No more entries in PROMPTS.txt. Finished.")
            return 0

        cycle_start = time.time()
        deadline = cycle_start + MAX_CYCLE_SECONDS
        start_cycle_log(load_pointer(), cycle_no)      # one log file per index/cycle
        print("\n" + "=" * 60)
        print(f"Cycle {cycle_no} of {NUM_CYCLES} started. Limit: {MAX_CYCLE_SECONDS // 60} min.")

        try:
            result = step3(deadline)
            if result is None:
                return 1
            index, _ = result

            # wait for the reply; if the time limit runs out, stop/resend instead of terminating
            resends = 0
            while True:
                try:
                    if not wait_for_response(deadline):
                        return 1
                    break
                except CycleTimeout:
                    resends += 1
                    if resends > MAX_RESEND_RETRIES:
                        print(f"Time limit reached again after {MAX_RESEND_RETRIES} resend(s) - giving up.")
                        raise
                    print(f"TIME LIMIT of {MAX_CYCLE_SECONDS}s reached without a finished reply - "
                          f"recovery attempt {resends} of {MAX_RESEND_RETRIES}.")
                    deadline = time.time() + MAX_CYCLE_SECONDS      # fresh time limit
                    if not recover_and_resend(index, deadline):
                        print("Stopped: recovery failed.")
                        return 1
                    print("Recovery done - waiting for the response again.")
        except CycleTimeout:
            print(f"TERMINATED: the cycle ran longer than {MAX_CYCLE_SECONDS}s without finishing.")
            return 2

        save_pointer(index + 1)
        print(f"Pointer advanced: [{index:04d}] -> [{index + 1:04d}]. "
              f"Cycle took {time.time() - cycle_start:.0f}s.")

        if not prompt_exists(index + 1):
            print(f"[{index:04d}] was the last entry in PROMPTS.txt. Finished.")
            return 0

    print(f"Completed {NUM_CYCLES} cycle(s). Finished.")
    return 0


def main() -> int:
    """Runs the cycles; writes any crash traceback and the exit code into the current log."""
    LIVE.start()
    rc = None
    try:
        rc = _run()
        return rc
    except BaseException:
        rc = "EXCEPTION (see traceback above)"
        tb = traceback.format_exc()
        _log_write("\n!!! UNHANDLED EXCEPTION !!!\n" + tb + "\n")
        UI_Q.put("\n!!! UNHANDLED EXCEPTION !!!\n" + tb + "\n")
        raise
    finally:
        note = (f"RUN ENDED at {_ts()} - exit code: {rc}  "
                f"(0 = finished, 1 = stopped/failed step, 2 = cycle timeout)")
        stop_cycle_log(note)
        UI_Q.put("\n" + note + "\n")
        close_live_window(is_error=(rc != 0))   # red + 2 s hold on any error


if __name__ == "__main__":
    sys.exit(main())