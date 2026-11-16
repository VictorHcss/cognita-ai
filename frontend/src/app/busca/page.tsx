import { Search } from "lucide-react";
import type { Metadata } from "next";
import { SemanticSearch } from "@/components/search/SemanticSearch";
import { PageHeader } from "@/components/ui";

export const metadata: Metadata = { title: "Busca" };

export default function BuscaPage() {
  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Busca semântica"
        icon={Search}
        description="Encontra trechos pelo significado da pergunta, não pelas palavras exatas. A pontuação é a similaridade de cosseno entre os vetores."
      />
      <SemanticSearch />
    </div>
  );
}
