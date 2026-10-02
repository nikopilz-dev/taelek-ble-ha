"""Record selected ecoControl HBC instructions without distributing the app."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "evidence/ecocontrol-3.0.11/index.android.bundle"
TOOL = ROOT / "tools/hermes-decomp-download/hermes-decomp.exe"


def main():
    selected = []
    for function in (1294, 7451, 8129, 11329, 13718):
        result = subprocess.run(
            [
                str(TOOL),
                "disasm",
                str(BUNDLE),
                "--function",
                str(function),
                "--info",
                "--show-offsets",
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        selected.append(result.stdout)
    (ROOT / "evidence/ecocontrol-selected-disassembly.txt").write_text(
        "\n".join(selected), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
