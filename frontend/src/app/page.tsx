import Link from "next/link";
import { getHealth, type HealthResponse } from "@/lib/api";
import { MODULES } from "@/lib/modules";

export const dynamic = "force-dynamic";

async function loadHealth(): Promise<HealthResponse | null> {
  try {
    return await getHealth();
  } catch {
    return null;
  }
}

export default async function Home() {
  const health = await loadHealth();

  return (
    <div className="max-w-4xl space-y-8">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Cognita AI</h1>
        <p className="mt-1 text-neutral-500">Conhecimento conectado. Inteligência aplicada.</p>
      </header>

      <section className="rounded-lg border border-neutral-200 p-4 text-sm dark:border-neutral-800">
        <h2 className="mb-2 font-medium">Status do backend</h2>
        {health ? (
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-4">
            <dt className="text-neutral-500">API</dt>
            <dd className="text-emerald-600">● online (v{health.version})</dd>
            <dt className="text-neutral-500">Ambiente</dt>
            <dd>{health.env}</dd>
            <dt className="text-neutral-500">LLM</dt>
            <dd className="font-mono">{health.llm_provider}</dd>
            <dt className="text-neutral-500">Embeddings</dt>
            <dd className="font-mono">{health.embedding_provider}</dd>
          </dl>
        ) : (
          <p className="text-red-600">
            ● offline — rode <code className="font-mono">uvicorn app.main:app --reload</code> em
            backend/
          </p>
        )}
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
        {MODULES.map((m) => (
          <Link
            key={m.href}
            href={m.href}
            className="rounded-lg border border-neutral-200 p-4 transition hover:border-indigo-400 dark:border-neutral-800"
          >
            <div className="flex items-center justify-between">
              <h3 className="font-medium">{m.label}</h3>
              <span className="text-xs text-neutral-500">Etapa {m.stage}</span>
            </div>
            <p className="mt-1 text-sm text-neutral-500">{m.description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
