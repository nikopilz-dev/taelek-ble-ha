import json
from pathlib import Path


def test_hacs_repository_layout():
    root = Path(__file__).resolve().parents[1]
    hacs = json.loads((root / "hacs.json").read_text(encoding="utf-8"))
    assert hacs["name"] == "Taelek BLE"
    assert hacs["render_readme"] is True
    assert not hacs.get("content_in_root", False)
    assert not hacs.get("zip_release", False)
    components = [path.name for path in (root / "custom_components").iterdir() if path.is_dir()]
    assert components == ["taelek"]
    assert (root / "custom_components/taelek/manifest.json").is_file()


def test_bundled_library_matches_source():
    root = Path(__file__).resolve().parents[1]
    for source in (root / "src/taelek_ble").glob("*.py"):
        bundled = root / "custom_components/taelek/taelek_ble" / source.name
        assert bundled.read_bytes() == source.read_bytes(), f"Rebundle {source.name}"


def test_bluetooth_dependencies_use_home_assistant_versions():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "custom_components/taelek/manifest.json").read_text(encoding="utf-8")
    )
    # Core Bluetooth supplies Bleak and bleak-retry-connector under HA's constraints.
    assert {"bluetooth", "bluetooth_adapters"} <= set(manifest["dependencies"])
    assert not any(
        requirement.startswith(("bleak", "habluetooth")) for requirement in manifest["requirements"]
    )


def test_manifest_and_translation_schema():
    root = Path(__file__).resolve().parents[1] / "custom_components/taelek"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "taelek"
    assert manifest["config_flow"] and "bluetooth_adapters" in manifest["dependencies"]
    assert all(matcher["connectable"] is False for matcher in manifest["bluetooth"])
    for matcher in manifest["bluetooth"]:
        if "local_name" in matcher:
            assert matcher["local_name"] == "Tael*"
            assert not any(char in matcher["local_name"][:3] for char in "*?[")
    strings = json.loads((root / "strings.json").read_text(encoding="utf-8"))
    assert "protocol_profile" not in strings["options"]["step"]["init"]["data"]
    for path in (root / "translations").glob("*.json"):
        translation = json.loads(path.read_text(encoding="utf-8"))
        assert translation["config"]["abort"].keys() == strings["config"]["abort"].keys()
        assert (
            translation["options"]["step"]["init"]["data"].keys()
            == strings["options"]["step"]["init"]["data"].keys()
        )
