export type AppModule = {
  href: string;
  label: string;
  description: string;
  stage: number;
};

export const MODULES: AppModule[] = [
  {
    href: "/biblioteca",
    label: "Biblioteca",
    description: "Upload, coleções e processamento de documentos.",
    stage: 2,
  },
  {
    href: "/busca",
    label: "Busca",
    description: "Encontre trechos pelo significado, com pontuação de similaridade.",
    stage: 4,
  },
  {
    href: "/chat",
    label: "Chat",
    description: "Converse com suas bases de conhecimento, com fontes.",
    stage: 6,
  },
  {
    href: "/lab/rag",
    label: "Laboratório RAG",
    description: "Chunks, scores de similaridade e contexto enviado à LLM.",
    stage: 7,
  },
  {
    href: "/lab/llm",
    label: "Laboratório LLM",
    description: "Compare modelos, prompts, tokens e latência.",
    stage: 8,
  },
];
