import {
  Cpu,
  FlaskConical,
  LayoutDashboard,
  Library,
  type LucideIcon,
  MessagesSquare,
  Search,
} from "lucide-react";

/** Etapa do roadmap já concluída — módulos até aqui estão disponíveis. */
export const CURRENT_STAGE = 5;

export type AppModule = {
  href: string;
  label: string;
  description: string;
  stage: number;
  icon: LucideIcon;
  group: "Conhecimento" | "Laboratórios";
};

export const HOME = { href: "/", label: "Visão geral", icon: LayoutDashboard };

export const MODULES: AppModule[] = [
  {
    href: "/biblioteca",
    label: "Biblioteca",
    description: "Upload, coleções e processamento de documentos.",
    stage: 2,
    icon: Library,
    group: "Conhecimento",
  },
  {
    href: "/busca",
    label: "Busca",
    description: "Encontre trechos pelo significado, com pontuação de similaridade.",
    stage: 4,
    icon: Search,
    group: "Conhecimento",
  },
  {
    href: "/chat",
    label: "Chat",
    description: "Pergunte aos seus documentos e receba respostas com as fontes citadas.",
    stage: 5,
    icon: MessagesSquare,
    group: "Conhecimento",
  },
  {
    href: "/lab/rag",
    label: "Laboratório RAG",
    description: "Chunks, scores de similaridade e contexto enviado à LLM.",
    stage: 7,
    icon: FlaskConical,
    group: "Laboratórios",
  },
  {
    href: "/lab/llm",
    label: "Laboratório LLM",
    description: "Compare modelos, prompts, tokens e latência.",
    stage: 8,
    icon: Cpu,
    group: "Laboratórios",
  },
];

export const isAvailable = (m: AppModule) => m.stage <= CURRENT_STAGE;
