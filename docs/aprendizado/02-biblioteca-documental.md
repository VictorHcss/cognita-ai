# Etapa 2 — Biblioteca documental

## Conceito estudado
Ingestão de documentos: a primeira metade do pipeline RAG (receber → armazenar →
extrair → limpar). Chunking e embeddings vêm na Etapa 3.

## Problema que resolve
Cada formato guarda texto de um jeito (PDF em páginas com coordenadas, DOCX em
parágrafos XML, TXT em bytes com encoding desconhecido). O RAG precisa de texto
limpo **e** da referência de origem (documento + página) para citar fontes.

## Tecnologias
- **SQLAlchemy 2 + Alembic**: modelos tipados e migrations versionadas.
- **PyMuPDF** (PDF), **python-docx** (DOCX), decodificação UTF-8 → CP1252 (TXT/MD).
- **FastAPI BackgroundTasks**: o processamento roda depois da resposta do upload.
- **Postgres + pgvector** via Docker no desenvolvimento.

## Decisões
- **Docker local agora, Supabase depois.** Desenvolvimento offline, testes rápidos
  e banco descartável. Migrar = trocar `DATABASE_URL` e `STORAGE_BACKEND`.
- **Storage atrás de interface** (`FileStorage`): `LocalStorage` (disco) e
  `SupabaseStorage` (API REST). Mesmo padrão dos provedores de IA.
- **Texto salvo por página** (`document_pages`). Assim cada chunk futuro herda o
  número da página — essencial para "fonte: arquivo.pdf, p. 12".
- **Status explícito** (`uploaded → processing → processed | failed`) com a
  mensagem de erro gravada. A UI atualiza sozinha enquanto há itens pendentes.
- **Deduplicação por SHA-256** dentro da coleção: o mesmo arquivo não entra 2×.
- **DOCX vira "página 1"**: o formato não guarda paginação (ela depende do Word
  renderizar o documento).

## Funcionamento
1. `POST /api/documents` valida tipo, tamanho e duplicidade, salva o original em
   `{id}/original.{ext}` e cria o registro com status `uploaded`.
2. Em segundo plano, `process_document` lê o arquivo, extrai por página, aplica
   `clean_text` (NFC, remove controle, junta hifenização, colapsa espaços) e grava
   as páginas. Reprocessar substitui as páginas (idempotente).
3. PDF sem texto (escaneado) termina como `failed` com explicação — OCR fica para
   depois.

## Testes realizados
- 20 testes automatizados: extração de cada formato, limpeza, CRUD de coleções,
  upload → processamento, rejeições (415/400/409), falha + reprocessamento, exclusão
  removendo o arquivo do disco.
- Teste manual no navegador: criar coleção, enviar arquivos, ver texto por página,
  reprocessar e excluir.

## Possíveis melhorias
- OCR para PDFs escaneados.
- Fila dedicada (ex.: arq/Celery) se documentos grandes ficarem lentos.
- Testar o `SupabaseStorage` contra um projeto real.
