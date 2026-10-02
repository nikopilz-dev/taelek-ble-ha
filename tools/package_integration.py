"""Create an installable ZIP with only custom-component runtime files."""

import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
component = root / "custom_components/taelek"
source = root / "src/taelek_ble"
for module in source.glob("*.py"):
    if module.read_bytes() != (component / "taelek_ble" / module.name).read_bytes():
        raise SystemExit("Bundled library is out of date; run tools/vendor_library.py first")
destination = root / "dist/taelek-ble-0.1.0.zip"
destination.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(component.rglob("*")):
        if path.is_file() and path.suffix in (".py", ".json"):
            archive.write(path, path.relative_to(root))
print(destination)
