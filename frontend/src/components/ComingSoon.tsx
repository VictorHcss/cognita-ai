import { Construction } from "lucide-react";
import { EmptyState, PageHeader } from "@/components/ui";
import { MODULES } from "@/lib/modules";

export function ComingSoon({ href }: { href: string }) {
  const mod = MODULES.find((m) => m.href === href);
  if (!mod) return null;
  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader title={mod.label} description={mod.description} icon={mod.icon} />
      <EmptyState icon={Construction} title="Em construção">
        Este módulo está previsto para a Etapa {mod.stage} do roadmap.
      </EmptyState>
    </div>
  );
}
