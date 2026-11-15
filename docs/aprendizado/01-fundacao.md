# Etapa 1 — Fundação

## Conceito estudado
Arquitetura em camadas e o padrão *Adapter* (porta/adaptador) aplicado a provedores de IA.

## Problema que resolve
Cada provedor (Gemini, OpenAI, Groq, Ollama) tem SDK, formato de mensagem e
contagem de tokens diferentes. Se o pipeline RAG chamar os SDKs diretamente, trocar
de provedor exige reescrever regras de negócio.

## Tecnologias
FastAPI, Pydantic Settings, Python `Protocol`, Next.js (App Router), Tailwind CSS.

## Decisões
- `Protocol` em vez de classes abstratas: qualquer classe com os métodos certos é
  um provedor válido (tipagem estrutural), o que facilita testes.
- Respostas da LLM retornam `LLMResult` com tokens e latência — já pensando no
  Laboratório de LLMs (Etapa 7/8).
- Provedor `fake` determinístico: permite testar o pipeline inteiro sem rede.

## Funcionamento
`providers/registry.py` lê `LLM_PROVIDER` / `EMBEDDING_PROVIDER` do `.env` e
devolve a implementação correspondente. Os serviços recebem o provedor por
injeção de dependência do FastAPI.

## Testes realizados
- `GET /api/health` responde e informa os provedores configurados.
- Provedor fake gera embeddings determinísticos e normalizados.

## Possíveis melhorias
- Adicionar adaptadores reais (Etapa 3 para embeddings, Etapa 5 para LLM).
