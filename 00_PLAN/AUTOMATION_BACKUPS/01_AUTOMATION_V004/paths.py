import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "PROMPTS.txt")
OUTPUT_FILE = os.path.join(BASE_DIR, "FILE_CHECK.TXT")

def parse(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    rows = []
    current_index = None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # Match index line like: [0001]
        m = re.match(r"^\[(\d+)\]$", line)
        if m:
            current_index = m.group(1)
            continue

        # Match the "YES THE NEXT IS ..." line
        if line.startswith("YES THE NEXT IS "):
            full = line[len("YES THE NEXT IS "):].strip()
            if "\\" in full:
                folder, last = full.rsplit("\\", 1)
            else:
                folder, last = "", full

            # filename = text before the first space
            filename = last.split(" ", 1)[0]
            rows.append((current_index, folder, filename + ".docx"))

    return rows

def main():
    rows = parse(INPUT_FILE)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("|INDEX|PATH|FILENAME.DOCX|\n")
        for idx, folder, fname in rows:
            f.write(f"|{idx}|{folder}|{fname}|\n")
    print(f"Done. {len(rows)} rows written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()