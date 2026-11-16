import pytest

from app.processing.chunking import chunk_pages


def test_short_document_is_single_chunk() -> None:
    chunks = chunk_pages([(1, "Texto curto.")], chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "Texto curto."
    assert (chunks[0].page_start, chunks[0].page_end) == (1, 1)


def test_chunks_respect_size_and_prefer_sentence_boundaries() -> None:
    text = " ".join(f"Frase número {i} sobre recuperação de informação." for i in range(60))
    chunks = chunk_pages([(1, text)], chunk_size=200, overlap=40)
    assert len(chunks) > 5
    assert all(len(c.text) <= 200 for c in chunks)
    assert all(c.text.endswith(".") for c in chunks)  # cortou em fim de frase
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_overlap_repeats_end_of_previous_chunk() -> None:
    text = " ".join(f"Sentença {i}." for i in range(200))
    chunks = chunk_pages([(1, text)], chunk_size=120, overlap=30)
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        assert nxt.char_start < prev.char_end  # há sobreposição
        assert nxt.char_start > prev.char_start  # mas sempre avança


def test_overlap_works_with_large_paragraphs() -> None:
    # Cada página é um parágrafo grande que cabe sozinho num chunk: antes, isso zerava o overlap.
    page = " ".join(f"Frase {i} do capitulo." for i in range(40))  # ~900 caracteres
    chunks = chunk_pages([(1, page), (2, page)], chunk_size=1000, overlap=150)
    assert len(chunks) >= 2
    first, second = chunks[0], chunks[1]
    assert 0 < first.char_end - second.char_start <= 150
    assert second.text.startswith("Frase")  # recomeça no início de uma frase
    assert (second.page_start, second.page_end) == (1, 2)  # atravessa a página


def test_page_ranges_are_tracked() -> None:
    pages = [(1, "A" * 50 + "."), (2, "Segunda página."), (3, ""), (4, "Quarta página.")]
    chunks = chunk_pages(pages, chunk_size=1000, overlap=0)
    assert len(chunks) == 1
    assert (chunks[0].page_start, chunks[0].page_end) == (1, 4)

    small = chunk_pages(pages, chunk_size=60, overlap=0)
    assert small[0].page_start == 1
    assert small[-1].page_end == 4
    assert any(c.page_start == 2 for c in small)


def test_chunk_text_matches_offsets_in_full_text() -> None:
    pages = [(1, "Um parágrafo.\n\nOutro parágrafo."), (2, "Mais texto aqui.")]
    full = "Um parágrafo.\n\nOutro parágrafo.\n\nMais texto aqui."
    for c in chunk_pages(pages, chunk_size=20, overlap=5):
        assert full[c.char_start : c.char_end] == c.text


def test_long_word_is_hard_split() -> None:
    chunks = chunk_pages([(1, "x" * 250)], chunk_size=100, overlap=0)
    assert [len(c.text) for c in chunks] == [100, 100, 50]


def test_empty_document_and_invalid_params() -> None:
    assert chunk_pages([(1, "   "), (2, "")]) == []
    with pytest.raises(ValueError):
        chunk_pages([(1, "x")], chunk_size=100, overlap=100)
