import { Library as LibraryIcon } from "lucide-react";
import type { Metadata } from "next";
import { Library } from "@/components/library/Library";
import { PageHeader } from "@/components/ui";

export const metadata: Metadata = { title: "Biblioteca" };

export default function BibliotecaPage() {
  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Biblioteca"
        icon={LibraryIcon}
        description="Envie documentos, organize em coleções e confira o texto extraído e os chunks gerados."
      />
      <Library />
    </div>
  );
}
