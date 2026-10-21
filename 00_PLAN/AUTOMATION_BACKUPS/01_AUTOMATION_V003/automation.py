import ctypes
import json
import re
import subprocess
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import mss
import numpy as np
import pyperclip

# ---------------- SETTINGS ----------------
SCRIPT_DIR     = Path(__file__).resolve().parent
POINTER_FILE   = Path(r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\pointer.json")
PROMPTS_FILE   = str(SCRIPT_DIR / "PROMPTS.txt")
EXTRA_FILE     = str(SCRIPT_DIR / "FIX_PROMPT.txt")

AHK_EXE        = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
AHK_SCRIPT     = str(SCRIPT_DIR / "executor.ahk")
CHATGPT_WINDOW = "ahk_exe ChatGPT.exe"

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
SEND_BUTTON_IMG   = str(SCRIPT_DIR / "SEND_BUTTON.PNG")
SEND_THRESHOLD    = 0.80
SEND_RETRY_WAIT   = 2.0          # seconds to wait before searching again if not found
SEND_MAX_TRIES    = 2            # first try + one retry after SEND_RETRY_WAIT
SEND_PRE_WAIT     = 0.4          # small pause after paste so the send button can appear

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


# ---------- pointer + prompts ----------
def load_pointer() -> int:
    data = json.loads(POINTER_FILE.read_text(encoding="utf-8"))
    return int(data["index"])


def get_prompt(index: int) -> str:
    """Return only the prompt text of block [index] (no number, no separator)."""
    text = Path(PROMPTS_FILE).read_text(encoding="utf-8-sig")
    for block in re.split(r"\r?\n-{20,}\r?\n", text):
        m = re.match(rf"\s*\[{index:04d}\]\r?\n(.*)", block.strip(), re.DOTALL)
        if m:
            return m.group(1).strip()
    raise ValueError(f"Prompt [{index:04d}] not found in {PROMPTS_FILE}")


def expected_topic(prompt: str):
    """From line 1 'YES THE NEXT IS <path>\\<topic> - <desc>' return (full_path, label)."""
    line1 = prompt.splitlines()[0]
    full = re.sub(r"^\s*YES THE NEXT IS\s+", "", line1, flags=re.I).strip()
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


# ---------- vision ----------
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


def find_send_button(win_x, win_y, win_w, win_h):
    """Find SEND_BUTTON.PNG in the bottom part of the ChatGPT window. Returns (x, y) or None."""
    if not Path(SEND_BUTTON_IMG).exists():
        print(f"Missing send button image: {SEND_BUTTON_IMG}")
        return None

    top = win_y + int(win_h * (1 - SEARCH_BOTTOM_FRACTION))
    region = {"left": win_x, "top": top, "width": win_w, "height": win_y + win_h - top}

    tpl = cv2.imread(SEND_BUTTON_IMG, cv2.IMREAD_GRAYSCALE)
    with MSS() as sct:
        shot = np.array(sct.grab(region))
    gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
    if gray.shape[0] < tpl.shape[0] or gray.shape[1] < tpl.shape[1]:
        return None

    res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    print(f"Send button match score: {score:.2f}")
    if score < SEND_THRESHOLD:
        return None
    return (region["left"] + loc[0] + tpl.shape[1] // 2,
            region["top"] + loc[1] + tpl.shape[0] // 2)


def click_send_button(win_x, win_y, win_w, win_h) -> bool:
    """Locate the send button (retrying after a wait) and click it."""
    for attempt in range(1, SEND_MAX_TRIES + 1):
        pos = find_send_button(win_x, win_y, win_w, win_h)
        if pos is not None:
            print(f"Clicking send button at {pos}")
            ahk("click", pos[0], pos[1])
            return True
        if attempt < SEND_MAX_TRIES:
            print(f"Send button not found - waiting {SEND_RETRY_WAIT:.0f}s and trying again.")
            time.sleep(SEND_RETRY_WAIT)
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


# ---------- main step ----------
def step3() -> bool:
    # 1. pointer -> prompt + expected topic
    index = load_pointer()
    prompt = get_prompt(index)
    full_path, label = expected_topic(prompt)
    print(f"Pointer: [{index:04d}]  Expected: {full_path}")

    # 2. bring ChatGPT forward, locate the input bar
    wx, wy, ww, wh = map(int, ahk("activate", CHATGPT_WINDOW).split())
    print(f"ChatGPT window: x={wx} y={wy} w={ww} h={wh}")
    time.sleep(0.5)
    bx, by = find_input_bar(wx, wy, ww, wh)

    # 3. copy ChatGPT's last reply via its copy icon
    copied = copy_chatgpt_reply(wx, wy, ww, by)
    if copied is None:
        print("Stopped: could not copy the reply. Nothing pasted.")
        return False
    Path(COPIED_DEBUG_FILE).write_text(copied, encoding="utf-8")
    print(f"Copied {len(copied)} characters.")

    # 4. DOCX: look up index-1 in FILE_CHECK.TXT; skip if the file exists, else generate.
    #    (The clipboard still holds the copied reply, which the formatter reads.)
    if not ensure_docx(index):
        print("Stopped: DOCX check/generation failed. Nothing pasted.")
        return False

    # 5. verify the end of the reply against the pointer's topic
    if not verify(copied, full_path, label):
        print("Stopped: on-screen topic does not match the pointer. Nothing pasted.")
        return False
    print("MATCH confirmed.")

    # 6. clipboard -> input bar -> paste
    pyperclip.copy(build_clipboard_text(prompt))
    print(f"Clipboard set for prompt [{index:04d}]. Clicking input bar at ({bx}, {by})")
    ahk("click", bx, by)
    time.sleep(0.3)
    ahk("paste")

    # 7. click the send button (wait 2s and retry once if it isn't visible yet)
    time.sleep(SEND_PRE_WAIT)
    return click_send_button(wx, wy, ww, wh)


if __name__ == "__main__":
    sys.exit(0 if step3() else 1)