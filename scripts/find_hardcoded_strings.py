import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "Command" / "waifu_gacha.py"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

vn_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)

hardcoded = []
for idx, line in enumerate(lines, start=1):
    stripped = line.strip()
    if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith('*'):
        continue
    if vn_chars.search(line):
        hardcoded.append((idx, stripped))

print(f"Total lines with Vietnamese in waifu_gacha.py: {len(hardcoded)}")
for idx, s in hardcoded[:50]:
    print(f"L{idx}: {s}")

