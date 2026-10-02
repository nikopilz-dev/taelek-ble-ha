"""Preserve selected model and instruction evidence with reproducible references."""

import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lines = (root / "evidence/decompiled-2.0.3.js").read_text(encoding="utf-8").splitlines()
ranges = [
    (110372, 110394),
    (110420, 110472),
    (121495, 121568),
    (121808, 121856),
    (121878, 121932),
    (121950, 122009),
    (137326, 137376),
    (137825, 137850),
    (138165, 138264),
]
output = []
for first, last in ranges:
    module = next(
        (line for line in reversed(lines[:first]) if line.startswith("// === Module")), ""
    )
    output.append(f"\n{module}\nStable decompilation lines {first}-{last}:\n")
    output.extend(lines[first - 1 : last])
(root / "evidence/v2-model-excerpts.txt").write_text("\n".join(output), encoding="utf-8")
assembly = (root / "evidence/disassembly-2.0.3.txt").read_text(encoding="utf-8")
functions = {
    8385,
    8408,
    8409,
    8410,
    8411,
    8418,
    8442,
    8565,
    8566,
    8569,
    8570,
    8588,
    9130,
    9131,
    7951,
    7952,
    7964,
}
selected = []
for block in re.split(r"(?=; fn#)", assembly):
    match = re.match(r"; fn#(\d+)", block)
    if match and int(match[1]) in functions:
        selected.append(block)
(root / "evidence/v2-selected-disassembly.txt").write_text("\n".join(selected), encoding="utf-8")
print("Saved compact model excerpts and selected function disassembly")
