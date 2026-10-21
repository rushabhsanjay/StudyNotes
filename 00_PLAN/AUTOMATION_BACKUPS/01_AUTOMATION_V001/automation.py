import ctypes
import re
import subprocess
import time
from pathlib import Path

import cv2
import mss
import numpy as np
import pyperclip

# ---------------- SETTINGS ----------------
PROMPTS_FILE   = r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\PROMPTS.txt"            # <- your exported prompts file
EXTRA_FILE     = r"D:\00_ADMIN_FILES\05_CHATGPT_PROMPT.txt"
PROMPT_INDEX   = 162

AHK_EXE        = r"C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe"
AHK_SCRIPT     = r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\executor.ahk"
CHATGPT_WINDOW = "ahk_exe ChatGPT.exe"                       # check the exe name in Task Manager

TEMPLATE_IMG   = r"D:\03_STUDY_FOR_CAREER\00_PLAN\01_AUTOMATION\input_bar.png"                            # small crop of the placeholder text
MATCH_THRESHOLD = 0.70
SEARCH_BOTTOM_FRACTION = 0.35                                # search only the bottom 35% of the window
FALLBACK_FROM_BOTTOM = 70                                    # px above window bottom, used if no match

JOINER = "\n\n"                                              # between prompt and extra file
# ------------------------------------------

try:                                                         # make pixel coordinates match AHK
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


def get_prompt(index: int) -> str:
    """Return only the prompt text of block [index] (no number, no separator)."""
    text = Path(PROMPTS_FILE).read_text(encoding="utf-8-sig")
    for block in re.split(r"\r?\n-{20,}\r?\n", text):
        m = re.match(rf"\s*\[{index:04d}\]\r?\n(.*)", block.strip(), re.DOTALL)
        if m:
            return m.group(1).strip()
    raise ValueError(f"Prompt [{index:04d}] not found in {PROMPTS_FILE}")


def build_clipboard_text() -> str:
    prompt = get_prompt(PROMPT_INDEX)
    extra = Path(EXTRA_FILE).read_text(encoding="utf-8-sig").strip()
    return prompt + JOINER + extra


def ahk(*args) -> str:
    r = subprocess.run([AHK_EXE, AHK_SCRIPT, *map(str, args)],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if r.returncode != 0:
        raise RuntimeError(f"AHK failed ({out or r.stderr.strip()})")
    return out


def find_input_bar(win_x, win_y, win_w, win_h):
    """Return (x, y) screen coords to click. Template match first, fallback second."""
    top = win_y + int(win_h * (1 - SEARCH_BOTTOM_FRACTION))
    region = {"left": win_x, "top": top, "width": win_w, "height": win_y + win_h - top}

    if Path(TEMPLATE_IMG).exists():
        tpl = cv2.imread(TEMPLATE_IMG, cv2.IMREAD_GRAYSCALE)
        with mss.mss() as sct:
            shot = np.array(sct.grab(region))
        gray = cv2.cvtColor(shot, cv2.COLOR_BGRA2GRAY)
        if gray.shape[0] >= tpl.shape[0] and gray.shape[1] >= tpl.shape[1]:
            res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)
            print(f"Template match score: {score:.2f}")
            if score >= MATCH_THRESHOLD:
                return (region["left"] + loc[0] + tpl.shape[1] // 2,
                        region["top"] + loc[1] + tpl.shape[0] // 2)
        print("Template not matched - using fallback position.")
    else:
        print("No template image - using fallback position.")

    return win_x + win_w // 2, win_y + win_h - FALLBACK_FROM_BOTTOM


def step1():
    # 1. build text and put it on the clipboard
    pyperclip.copy(build_clipboard_text())
    print(f"Clipboard set for prompt [{PROMPT_INDEX:04d}].")

    # 2. switch to ChatGPT, get its window rectangle
    rect = ahk("activate", CHATGPT_WINDOW)
    wx, wy, ww, wh = map(int, rect.split())
    print(f"ChatGPT window: x={wx} y={wy} w={ww} h={wh}")
    time.sleep(0.5)

    # 3. locate input bar, click it, paste
    x, y = find_input_bar(wx, wy, ww, wh)
    print(f"Clicking input bar at ({x}, {y})")
    ahk("click", x, y)
    time.sleep(0.3)
    ahk("paste")


if __name__ == "__main__":
    step1()