"""Divisão do documento em chunks, preservando páginas e posições.

Estratégia ("recursiva por separadores", com sobreposição):
1. As páginas são unidas num texto único; guardamos onde cada página começa.
2. O texto é quebrado em unidades pequenas, preferindo cortar em parágrafos,
   depois linhas, depois frases, depois espaços — só corta palavras em último caso.
3. Unidades vizinhas são agrupadas até `chunk_size` caracteres.
4. Cada chunk recomeça com ~`overlap` caracteres do anterior, para que uma ideia
   cortada na fronteira apareça inteira em pelo menos um chunk.

Como trabalhamos com offsets (posições) no texto completo, cada chunk sabe
exatamente em quais páginas começa e termina — base das citações do RAG.
"""

import re
from bisect import bisect_right
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

PAGE_SEPARATOR = "\n\n"

# Do separador mais "forte" para o mais "fraco".
_SEPARATORS = [
    re.compile(r"\n\s*\n"),  # parágrafo
    re.compile(r"\n"),  # linha
    re.compile(r"(?<=[.!?…;:])\s+"),  # frase
    re.compile(r"\s+"),  # palavra
]


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    char_start: int  # posição no texto completo do documento
    char_end: int
    page_start: int
    page_end: int

    @property
    def token_estimate(self) -> int:
        # Aproximação comum: ~4 caracteres por token. Suficiente para métricas.
        return max(1, len(self.text) // 4)


def _spans(
    text: str, start: int, end: int, max_len: int, level: int = 0
) -> Iterator[tuple[int, int]]:
    """Quebra text[start:end] em trechos de até max_len, cortando no melhor separador."""
    if end - start <= max_len:
        yield start, end
        return
    for depth in range(level, len(_SEPARATORS)):
        cuts = [
            m.end() for m in _SEPARATORS[depth].finditer(text, start, end) if start < m.end() < end
        ]
        if cuts:
            prev = start
            for cut in [*cuts, end]:
                yield from _spans(text, prev, cut, max_len, depth)
                prev = cut
            return
    for s in range(start, end, max_len):  # nenhum separador: corte rígido
        yield s, min(s + max_len, end)


def _trim(text: str, start: int, end: int) -> tuple[int, int]:
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def chunk_pages(
    pages: Sequence[tuple[int, str]], chunk_size: int = 1000, overlap: int = 150
) -> list[Chunk]:
    """Recebe [(número_da_página, texto)] e devolve chunks com páginas de origem."""
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser positivo.")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap deve estar entre 0 e chunk_size - 1.")

    page_numbers: list[int] = []
    page_starts: list[int] = []
    parts: list[str] = []
    offset = 0
    for number, page_text in pages:
        if not page_text.strip():
            continue
        if parts:
            parts.append(PAGE_SEPARATOR)
            offset += len(PAGE_SEPARATOR)
        page_numbers.append(number)
        page_starts.append(offset)
        parts.append(page_text)
        offset += len(page_text)
    full = "".join(parts)
    if not full:
        return []

    def page_at(pos: int) -> int:
        return page_numbers[max(0, bisect_right(page_starts, pos) - 1)]

    # Unidades de até 1/4 do chunk: granularidade suficiente para o overlap e para
    # um chunk terminar no meio de um parágrafo longo (sempre num separador).
    unit_size = max(1, chunk_size // 4)
    units = [u for u in _spans(full, 0, len(full), unit_size) if full[u[0] : u[1]].strip()]

    chunks: list[Chunk] = []
    i = 0  # primeira unidade do chunk atual
    pos = 0  # onde o chunk atual começa (pode ser no meio da unidade i, por causa do overlap)
    while i < len(units):
        start = max(pos, units[i][0])
        j = i
        while j < len(units) and units[j][1] - start <= chunk_size:
            j += 1
        j = max(j, i + 1)  # garante progresso
        s, e = _trim(full, start, units[j - 1][1])
        chunks.append(
            Chunk(
                index=len(chunks),
                text=full[s:e],
                char_start=s,
                char_end=e,
                page_start=page_at(s),
                page_end=page_at(max(s, e - 1)),
            )
        )
        if j >= len(units):
            break
        # O próximo chunk recomeça dentro dos últimos `overlap` caracteres deste,
        # num início de frase (ou palavra) — desde que ainda caiba a próxima unidade.
        pos = _overlap_start(full, s, e, overlap)
        if units[j][1] - pos > chunk_size:
            pos = units[j][0]
        i = next(k for k in range(i, j + 1) if units[k][1] > pos)
    return chunks


def _overlap_start(text: str, s: int, e: int, overlap: int) -> int:
    lo = max(s + 1, e - overlap)
    for pattern in (_SEPARATORS[2], _SEPARATORS[3]):  # frase, depois palavra
        match = pattern.search(text, lo, e)
        if match and match.end() < e:
            return match.end()
    return e
