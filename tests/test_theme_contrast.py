from home_maintenance_hub.ui.theme import assert_theme_contrast_aa


def test_mw_theme_meets_wcag_aa() -> None:
    assert_theme_contrast_aa()
