from app.utils.text_cleaner import clean_text


def test_clean_text_normalizations() -> None:
    """Verifies that unicode ligatures and spaces are cleaned up correctly."""
    raw = "John \u00a0 Doe \t \n\n\n\u201cAwesome candidate\u201d\n"
    expected = "John Doe\n\"Awesome candidate\""
    assert clean_text(raw) == expected


def test_clean_text_duplicate_lines() -> None:
    """Verifies sequential duplicate lines are stripped."""
    raw = "Software Engineer\nSoftware Engineer\nStanford University"
    expected = "Software Engineer\nStanford University"
    assert clean_text(raw) == expected


def test_clean_text_page_numbers() -> None:
    """Verifies page numbering templates are removed."""
    raw = "John Doe\nPage 1 of 3\nSkills: Python\n[ 2 / 3 ]\n2"
    expected = "John Doe\nSkills: Python"
    assert clean_text(raw) == expected


def test_clean_text_boilerplate() -> None:
    """Verifies confidential resume indicators are stripped."""
    raw = "Confidential Resume\nJane Smith\nAll Rights Reserved"
    expected = "Jane Smith"
    assert clean_text(raw) == expected
