# Arquitetura

## Visão geral

```
┌──────────────┐   HTTP/JSON   ┌─────────────────────────────────────────┐
│  Next.js     │ ────────────▶ │  FastAPI                                │
│  (frontend)  │               │  api/        rotas HTTP (finas)         │
└──────────────┘               │  services/   regras de negócio / RAG    │
                               │  providers/  adaptadores de IA          │
                               │  core/       config, logs, erros        │
                               └───────┬───────────────┬─────────────────┘
                                       │               │
                          ┌────────────▼───┐   ┌───────▼────────────────┐
                          │ PostgreSQL     │   │ APIs externas          │
                          │ + pgvector     │   │ Gemini · OpenAI · Groq │
                          │ (Supabase)     │   │ Ollama (opcional)      │
                          └────────────────┘   └────────────────────────┘
```

## Princípios

1. **Rotas finas.** A camada `api/` só valida entrada e chama `services/`.
2. **Provedores atrás de interfaces.** `providers/base.py` define `LLMProvider` e
   `EmbeddingProvider`. Os serviços dependem dessas interfaces, nunca de um SDK
   específico. Trocar Gemini por OpenAI = mudar uma variável de ambiente.
3. **LLM e embeddings são independentes.** Configurados separadamente
   (`LLM_PROVIDER`, `EMBEDDING_PROVIDER`).
4. **Segredos só no backend.** O frontend nunca vê chaves de API.
5. **Provedor `fake` para testes.** Determinístico, sem rede e sem custo.

## Decisões em aberto

| Tema | Opções | Quando decidir |
|---|---|---|
| Dimensão dos embeddings | 768 (Gemini) / 1536 (OpenAI) | Etapa 3 — a coluna `vector(n)` depende disso |
| ORM / migrations | **Decidido:** SQLAlchemy 2 + Alembic | Etapa 2 |
| Processamento assíncrono | **Decidido:** BackgroundTasks (fila se necessário) | Etapa 2 |
