import { MODULES } from "@/lib/modules";

export function ComingSoon({ href }: { href: string }) {
  const mod = MODULES.find((m) => m.href === href);
  if (!mod) return null;
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight">{mod.label}</h1>
      <p className="mt-1 text-neutral-500">{mod.description}</p>
      <p className="mt-6 rounded-md border border-dashed border-neutral-300 p-4 text-sm text-neutral-500 dark:border-neutral-700">
        Módulo previsto para a Etapa {mod.stage} do roadmap.
      </p>
    </div>
  );
}
