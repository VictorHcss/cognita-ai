import type { DocumentStatus } from "@/lib/api";
import { STATUS_LABEL, STATUS_STYLE } from "@/lib/format";

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}
    >
      {status === "processing" && (
        <span className="size-1.5 animate-pulse rounded-full bg-current" aria-hidden />
      )}
      {STATUS_LABEL[status]}
    </span>
  );
}
