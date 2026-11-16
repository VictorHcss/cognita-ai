import { SemanticSearch } from "@/components/search/SemanticSearch";

export default function BuscaPage() {
  return (
    <div className="max-w-4xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Busca semântica</h1>
        <p className="mt-1 text-neutral-500">
          Encontra trechos pelo significado da pergunta, não pelas palavras exatas. A pontuação é
          a similaridade de cosseno entre os vetores.
        </p>
      </header>
      <SemanticSearch />
    </div>
  );
}
