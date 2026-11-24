from home_maintenance_hub.domain.instructions import clean_instruction_text


def test_strips_home_inspection_boilerplate() -> None:
    raw = "From home inspection: service heating + A/C units 2x/year (spring + fall)."
    assert clean_instruction_text(raw) == ""


def test_strips_checklist_prefix_keeps_action() -> None:
    raw = "From example checklist: pour 1/4 cup white vinegar in drain pump tank to prevent clogs."
    assert clean_instruction_text(raw) == (
        "pour 1/4 cup white vinegar in drain pump tank to prevent clogs."
    )


def test_keeps_real_instruction() -> None:
    raw = "Test twice yearly (spring + fall). Replace batteries if needed."
    assert clean_instruction_text(raw) == raw


def test_strips_trailing_seasonal_suffix() -> None:
    raw = "Check for ants, termites, rodents. From seasonal checklist."
    assert clean_instruction_text(raw) == "Check for ants, termites, rodents."
