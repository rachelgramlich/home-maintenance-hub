from home_maintenance_hub.migration.keys import map_area, map_type, stable_key


def test_stable_key_normalizes() -> None:
    assert stable_key("  Foo ", "HVAC", "January") == "foo|hvac|january"


def test_area_mapping() -> None:
    assert map_area("Yard") == "Exterior"
    assert map_area("HVAC") == "HVAC"


def test_type_mapping() -> None:
    assert map_type("Prevent") == "Inspect/Test"
    assert map_type("Replace") == "Replace"
