import pytest
from pdf_inspector import inspect_text


def test_text_mode_runs(simple_pdf, capsys):
    inspect_text(simple_pdf, page_num=1)
    captured = capsys.readouterr()
    assert "Page 1" in captured.out


def test_text_mode_shows_content(simple_pdf, capsys):
    inspect_text(simple_pdf, page_num=1)
    captured = capsys.readouterr()
    assert "Hello World" in captured.out


def test_search_filter_match(simple_pdf, capsys):
    inspect_text(simple_pdf, page_num=1, search="Secret")
    captured = capsys.readouterr()
    assert "Secret phrase" in captured.out
    assert "Hello World" not in captured.out


def test_search_filter_no_match(simple_pdf, capsys):
    inspect_text(simple_pdf, page_num=1, search="zzznomatch")
    captured = capsys.readouterr()
    assert "No text blocks found" in captured.out


def test_invalid_page_raises(simple_pdf):
    with pytest.raises(ValueError, match="out of range"):
        inspect_text(simple_pdf, page_num=99)


def test_missing_input_raises():
    with pytest.raises(FileNotFoundError):
        inspect_text("nonexistent.pdf")
