"""Create an installable ZIP with only custom-component runtime files."""

import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
component = root / "custom_components/taelek"
source = root / "src/taelek_ble"
for module in source.glob("*.py"):
    if module.read_bytes() != (component / "taelek_ble" / module.name).read_bytes():
        raise SystemExit("Bundled library is out of date; run tools/vendor_library.py first")
version = json.loads((component / "manifest.json").read_text(encoding="utf-8"))["version"]
destination = root / f"dist/taelek-ble-{version}.zip"
destination.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(component.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".json", ".yaml"):
            archive.write(path, path.relative_to(root))
print(destination)
