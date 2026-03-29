import pytest
from pathlib import Path
from pdf_redactor import redact_areas, redact_text


def test_redact_area_creates_output(simple_pdf, out):
    count = redact_areas(simple_pdf, out, areas=[(1, 40, 90, 300, 120)])
    assert Path(out).exists()
    assert count == 1


def test_redact_multiple_areas(simple_pdf, out):
    areas = [(1, 40, 90, 300, 120), (1, 40, 120, 300, 150)]
    count = redact_areas(simple_pdf, out, areas=areas)
    assert count == 2


def test_redact_text_finds_term(simple_pdf, out):
    count = redact_text(simple_pdf, out, terms=["Hello World"])
    assert count >= 1


def test_redact_text_multiple_terms(simple_pdf, out):
    count = redact_text(simple_pdf, out, terms=["Hello World", "Secret phrase"])
    assert count >= 2


def test_redact_combined(simple_pdf, out):
    count = redact_areas(
        simple_pdf, out, areas=[(1, 40, 90, 300, 120)], terms=["Secret phrase"]
    )
    assert count >= 2


def test_no_areas_or_terms_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="at least one"):
        redact_areas(simple_pdf, out, areas=[])


def test_empty_terms_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="at least one"):
        redact_text(simple_pdf, out, terms=[])


def test_invalid_page_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="out of range"):
        redact_areas(simple_pdf, out, areas=[(99, 0, 0, 100, 100)])


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        redact_areas("nonexistent.pdf", out, areas=[(1, 0, 0, 100, 100)])
