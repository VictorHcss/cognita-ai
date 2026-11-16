# Etapa 4 — Busca semântica

## Conceito estudado
**Busca por vizinhos mais próximos** (*nearest neighbor search*): transformar a pergunta
em vetor e achar os chunks cujos vetores apontam na direção mais parecida.

## Problema que resolve
A busca por palavra-chave falha com sinônimos e paráfrases. "Quanto guardar para
**imprevistos**?" não contém nenhuma palavra de "reserva de **emergência**", mas o
significado é o mesmo — e os vetores capturam isso.

## Tecnologias
- pgvector: operador `<=>` (distância de cosseno) e índice HNSW.
- Gemini com `task="query"` (`RETRIEVAL_QUERY`) para a pergunta.

## Decisões
- **Similaridade = 1 − distância de cosseno.** Mais intuitivo (maior = melhor).
- **Nunca misturar modelos.** A busca só considera chunks com o mesmo `embedding_model`
  do provedor atual; se houver chunks de outro modelo, a API avisa para reprocessar.
- **`hnsw.ef_search = 100`** (padrão do pgvector é 40): um pouco mais preciso, ainda rápido.
- **`hnsw.iterative_scan = relaxed_order`** (pgvector ≥ 0.8) para filtros, e os resultados
  são reordenados no Python (o modo "relaxed" pode devolver fora de ordem).
- **`SET LOCAL`** + rollback no fim: os ajustes valem só para aquela busca.
- **Rota `POST /api/search`** com `top_k`, `collection_id`, `document_id`, `min_score`, e
  devolvendo tempos de embedding e de busca separados.

## Funcionamento
1. `embed([pergunta], task="query")` → vetor de 768 dimensões.
2. `SELECT ... ORDER BY embedding <=> :vetor LIMIT top_k`, com filtros e `embedding_model`.
3. Converte distâncias em similaridade, reordena, aplica `min_score`, numera o ranking.

## O que aprendemos sobre o planner do Postgres
Investigando um teste que "passava demais", vimos pelo `EXPLAIN` que:
- Com **filtro seletivo** (coleção pequena), o Postgres **não usa o HNSW**: encontra os
  poucos chunks da coleção pelo índice comum e calcula a distância **exata** de cada um.
  É a melhor estratégia nesse caso.
- Quando o **HNSW é usado** com filtro, ele busca os vizinhos e só depois filtra. Com
  `ef_search` pequeno e a coleção pequena "longe" na ordem, **sobram menos que top_k**.
  O teste `test_without_iterative_scan_hnsw_loses_filtered_results` demonstra o problema,
  e `test_hnsw_with_filter_fills_top_k_thanks_to_iterative_scan` mostra a correção.

## Avaliação de relevância
`app/evaluation/retrieval.py` calcula:
- **hit@k** — fração de perguntas com o trecho certo entre os k primeiros;
- **MRR** — média de 1/posição do primeiro acerto (premia acertar no topo).

Rodar (em `backend/`, com o `temas.md` enviado na Biblioteca):
```bash
python -m scripts.eval_retrieval evaluation/datasets/temas.json --verbose
```

Resultado com `gemini-embedding-001` (12 perguntas parafraseadas):

| hit@1 | hit@3 | hit@5 | MRR | latência média |
|---|---|---|---|---|
| 1,00 | 1,00 | 1,00 | 1,00 | ~1,3 s |

**Leitura crítica:** o resultado é perfeito, mas o conjunto é fácil — o `temas.md` tem só
3 chunks e assuntos muito distintos. Serve como teste de regressão, não como prova de
qualidade. A latência é quase toda a chamada ao Gemini; a busca no banco leva ~30 ms.

## Testes realizados
- 51 testes automatizados (busca exata com score 1, ordenação, top_k, filtros por coleção e
  documento, min_score, modelos diferentes não se misturam, validação, HNSW + filtros com
  1000 chunks, métricas hit@k/MRR).
- Teste manual na tela **Busca** com o Gemini real.

## Possíveis melhorias
- Chunks respeitando títulos do Markdown (hoje um chunk pode misturar dois temas).
- Conjunto de avaliação maior e mais difícil (documentos longos, assuntos próximos).
- Busca híbrida (vetor + palavra-chave) e reranking — Etapa 9.
- Cache do embedding de perguntas repetidas.
