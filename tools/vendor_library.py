"""Bundle the unpublished standalone library in the installable custom component."""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / "src" / "taelek_ble"
target = root / "custom_components" / "taelek" / "taelek_ble"
target.mkdir(parents=True, exist_ok=True)
for path in source.glob("*.py"):
    shutil.copyfile(path, target / path.name)
print(f"Bundled {len(list(source.glob('*.py')))} library modules")
