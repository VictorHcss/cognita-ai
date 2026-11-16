import { Badge, type BadgeTone } from "@/components/ui";
import type { DocumentStatus } from "@/lib/api";
import { STATUS_LABEL } from "@/lib/format";

const TONE: Record<DocumentStatus, BadgeTone> = {
  uploaded: "neutral",
  processing: "warning",
  processed: "success",
  failed: "danger",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <Badge tone={TONE[status]} pulse={status === "processing" || status === "uploaded"}>
      {STATUS_LABEL[status]}
    </Badge>
  );
}
