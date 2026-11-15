import pytest

from app.processing.cleaning import clean_text
from app.processing.extractors import ExtractionError, extract, file_type_from_name
from tests.factories import make_docx, make_pdf


@pytest.mark.parametrize(
    ("name", "expected"),
    [("a.PDF", "pdf"), ("b.docx", "docx"), ("c.markdown", "md"), ("d.txt", "txt"), ("e.exe", None)],
)
def test_file_type_from_name(name: str, expected: str | None) -> None:
    assert file_type_from_name(name) == expected


def test_pdf_keeps_page_numbers() -> None:
    pages = extract("pdf", make_pdf(["Primeira pagina", "Segunda pagina"]))
    assert [p.page_number for p in pages] == [1, 2]
    assert "Segunda pagina" in pages[1].text


def test_docx_extracts_paragraphs() -> None:
    pages = extract("docx", make_docx(["Introdução ao RAG", "Embeddings"]))
    assert len(pages) == 1
    assert "Introdução ao RAG" in pages[0].text


def test_plain_text_handles_latin1() -> None:
    pages = extract("txt", "ação".encode("cp1252"))
    assert pages[0].text == "ação"


def test_corrupted_pdf_raises() -> None:
    with pytest.raises(ExtractionError):
        extract("pdf", b"isto nao e um pdf")


def test_clean_text_normalizes() -> None:
    raw = "Conheci-\nmento   conectado\r\n\n\n\n\x00Inteligência\taplicada  "
    assert clean_text(raw) == "Conhecimento conectado\n\nInteligência aplicada"
