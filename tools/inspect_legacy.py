"""Print short legacy snippets without dumping the entire app."""

import re
from pathlib import Path

bundle = (
    Path(__file__).resolve().parents[1] / "evidence/MAI+Smart_1.0.17_APKPure/index.android.bundle"
)
text = bundle.read_text(encoding="utf-8")
for pattern in (r"readInt16LE\(0\)", r'"measuredFloor"===', r'"setPoint"===', r"&128", r"&240"):
    for match in list(re.finditer(pattern, text))[:5]:
        print(
            f"\nOffset {match.start()} ({pattern}):\n{text[max(0, match.start() - 200) : match.end() + 350]}"
        )
