import { ArrowUpRight, Boxes, FileText, FolderTree, Sparkles } from "lucide-react";
import Link from "next/link";
import { LogoMark } from "@/components/Logo";
import { Badge, Card, Stat } from "@/components/ui";
import {
  type Collection,
  type DocumentItem,
  getHealth,
  type HealthResponse,
  listCollections,
  listDocuments,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { CURRENT_STAGE, isAvailable, MODULES } from "@/lib/modules";

export const dynamic = "force-dynamic";

async function load(): Promise<{
  health: HealthResponse | null;
  docs: DocumentItem[];
  collections: Collection[];
}> {
  try {
    const [health, docs, collections] = await Promise.all([
      getHealth(),
      listDocuments(),
      listCollections(),
    ]);
    return { health, docs, collections };
  } catch {
    return { health: null, docs: [], collections: [] };
  }
}

export default async function Home() {
  const { health, docs, collections } = await load();
  const processed = docs.filter((d) => d.status === "processed").length;
  const failed = docs.filter((d) => d.status === "failed").length;
  const chunks = docs.reduce((sum, d) => sum + d.chunk_count, 0);
  const pages = docs.reduce((sum, d) => sum + d.page_count, 0);

  return (
    <div className="animate-fade-in space-y-8">
      <section className="relative overflow-hidden rounded-2xl border border-border bg-surface p-6 sm:p-8">
        <LogoMark className="pointer-events-none absolute -top-6 -right-6 size-48 opacity-[0.07]" />
        <p className="text-xs font-medium tracking-wider text-accent-text uppercase">
          Plataforma de engenharia de conhecimento
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-text sm:text-4xl">Cognita AI</h1>
        <p className="mt-2 max-w-xl text-muted">
          Conhecimento conectado. Inteligência aplicada.
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
          {health ? (
            <>
              <Badge tone="success" pulse>
                API online · v{health.version}
              </Badge>
              <Badge tone="accent">Embeddings: {health.embedding_provider}</Badge>
              <Badge tone="neutral">LLM: {health.llm_provider}</Badge>
              <Badge tone="neutral">Etapa {CURRENT_STAGE} de 9</Badge>
            </>
          ) : (
            <Badge tone="danger">
              API offline — rode <code className="font-mono">uvicorn app.main:app --reload</code>
            </Badge>
          )}
        </div>
      </section>

      <section aria-label="Indicadores" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat
          label="Documentos"
          value={docs.length}
          icon={FileText}
          hint={failed ? `${processed} processados · ${failed} com falha` : `${processed} processados`}
        />
        <Stat label="Chunks indexados" value={chunks} icon={Boxes} hint={`${pages} páginas extraídas`} />
        <Stat label="Coleções" value={collections.length} icon={FolderTree} />
        <Stat
          label="Vetores"
          value="768 d"
          icon={Sparkles}
          hint={health ? `${health.embedding_provider} · cosseno` : "—"}
        />
      </section>

      <section aria-labelledby="modulos" className="space-y-3">
        <h2 id="modulos" className="text-lg font-semibold text-text">
          Módulos
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {MODULES.map((m) => {
            const available = isAvailable(m);
            const Icon = m.icon;
            const body = (
              <Card
                className={cn(
                  "group h-full p-4 transition",
                  available ? "hover:border-primary/50 hover:shadow-md" : "opacity-70",
                )}
              >
                <div className="flex items-start justify-between">
                  <span
                    className={cn(
                      "flex size-9 items-center justify-center rounded-lg",
                      available ? "bg-primary-soft text-primary" : "bg-surface-2 text-muted",
                    )}
                  >
                    <Icon className="size-4.5" aria-hidden />
                  </span>
                  {available ? (
                    <ArrowUpRight
                      className="size-4 text-muted transition group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-primary"
                      aria-hidden
                    />
                  ) : (
                    <Badge tone="neutral">Etapa {m.stage}</Badge>
                  )}
                </div>
                <h3 className="mt-3 font-medium text-text">{m.label}</h3>
                <p className="mt-1 text-sm text-muted">{m.description}</p>
              </Card>
            );
            return available ? (
              <Link key={m.href} href={m.href} className="rounded-xl">
                {body}
              </Link>
            ) : (
              <div key={m.href}>{body}</div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
