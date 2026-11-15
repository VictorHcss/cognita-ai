"""Gera arquivos de exemplo em memória para os testes."""

import io

import docx
import pymupdf


def make_pdf(pages: list[str]) -> bytes:
    pdf = pymupdf.open()
    for content in pages:
        page = pdf.new_page()
        page.insert_text((72, 72), content)
    data = pdf.tobytes()
    pdf.close()
    return data


def make_docx(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
