# Etapa 3 — Chunking e embeddings

## Conceito estudado
- **Chunking**: dividir o documento em trechos do tamanho certo para busca e contexto.
- **Embeddings**: representar cada trecho como um vetor de números, de modo que
  textos com significado parecido fiquem próximos no espaço vetorial.

## Problema que resolve
Uma LLM não consegue ler uma apostila inteira a cada pergunta (custo, limite de
contexto, ruído). Precisamos de trechos pequenos o bastante para serem precisos e
grandes o bastante para terem sentido sozinhos. E precisamos achá-los por
**significado**, não por palavra exata — é isso que os embeddings permitem (Etapa 4).

## Tecnologias
- Chunker próprio em Python puro (`app/processing/chunking.py`).
- Gemini `gemini-embedding-001` via API REST (`app/providers/gemini.py`).
- pgvector: coluna `vector(768)` + índice **HNSW** com distância de cosseno.

## Decisões
- **Tamanho 1000 caracteres (~250 tokens), sobreposição 150.** Ponto de partida comum;
  ajustável por `.env` e será comparado no Laboratório RAG (Etapa 7).
- **Cortes "inteligentes".** O texto é quebrado preferindo parágrafo → linha → frase →
  palavra. Só corta palavras se não houver alternativa.
- **Chunks atravessam páginas.** Unimos as páginas e guardamos *offsets*, então cada
  chunk sabe `page_start`/`page_end` ("p. 3–4") e a posição exata no texto.
- **Sobreposição começa numa frase.** O próximo chunk recomeça no início de uma frase
  dentro dos últimos ~150 caracteres do anterior.
- **768 dimensões.** O Gemini gera até 3072; reduzir para 768 economiza 4× espaço com
  pouca perda de qualidade. Como a redução tira a normalização, normalizamos o vetor.
- **`task` na interface** (`document` vs `query`): o Gemini otimiza o vetor para o papel
  do texto. Os trechos usam `RETRIEVAL_DOCUMENT`; a pergunta (Etapa 4) usará `RETRIEVAL_QUERY`.
- **`embedding_model` salvo em cada chunk.** Vetores de modelos diferentes não são
  comparáveis; guardar a origem evita misturá-los sem perceber.
- **Falhas visíveis.** Sem chave, cota estourada (429, com novas tentativas) ou dimensão
  errada → documento fica "Falhou" com a explicação; as páginas extraídas são mantidas.

## Funcionamento
`process_document`: extrair → limpar → salvar páginas → `chunk_pages` →
`embed(task="document")` em lotes de 100 → salvar chunks com vetores → "Processado".
O log `document_processed` registra tempos de extração, chunking e embeddings.

## Testes realizados
- 39 testes automatizados, incluindo: limites de tamanho, cortes em fim de frase,
  sobreposição com parágrafos grandes, páginas de origem, offsets exatos, adaptador
  Gemini com API simulada (lotes, normalização, retry em 429, mensagens de erro) e o
  pipeline completo gravando vetores de 768 dimensões no pgvector.
- Teste manual: PDF de 5 páginas → 5 chunks com 90 caracteres de sobreposição e
  intervalos "p. 1–2", "p. 2–3"..., visíveis na aba **Chunks** do documento.

### Teste real com o Gemini
Documento com 4 assuntos (culinária, astronomia, finanças, futebol) e perguntas
**sem as palavras do texto**, buscando por similaridade de cosseno no pgvector:

| Pergunta | Trecho mais próximo | Similaridade |
|---|---|---|
| "Quanto dinheiro devo guardar para imprevistos?" | reserva de emergência (finanças) | 0,620 |
| "Como fazer um prato italiano de arroz cremoso?" | risoto (culinária) | 0,679 |
| "O que acontece quando uma estrela gigante morre?" | chunk com o colapso de estrelas | 0,580 |
| "Quantas vezes a seleção canarinho venceu o mundial?" | cinco títulos do Brasil | 0,682 |
| "Para que serve dividir documentos em trechos?" | "Chunking divide documentos em trechos" | 0,763 |

As 5 perguntas encontraram o trecho certo, mesmo com sinônimos ("imprevistos" →
"emergência", "seleção canarinho" → "Brasil").

**Observação importante:** com 1000 caracteres, os 4 assuntos viraram só 3 chunks, e
cada um misturava dois temas (ex.: culinária + início de astronomia). A busca acertou
mesmo assim, mas trechos misturados "diluem" o vetor e baixam a similaridade. Respeitar
títulos do Markdown como fronteira de chunk é uma melhoria natural.

### Problema encontrado e corrigido
A primeira versão não gerava sobreposição quando um parágrafo inteiro cabia num chunk
(o algoritmo só sabia recuar unidades inteiras). Solução: unidades menores (até 1/4 do
chunk) e recomeço no início de frase. Um teste cobre esse caso.

## Possíveis melhorias
- Contar tokens com o tokenizador real em vez da estimativa de 4 caracteres/token.
- Chunking semântico ou por estrutura (títulos do Markdown) — comparar na Etapa 7.
- Reprocessar só os embeddings ao trocar de modelo, sem reextrair o texto.
