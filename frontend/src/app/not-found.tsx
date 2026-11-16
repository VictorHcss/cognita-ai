import { FileQuestion } from "lucide-react";
import Link from "next/link";
import { buttonClasses, EmptyState } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="animate-fade-in py-10">
      <EmptyState icon={FileQuestion} title="Página não encontrada">
        <p>O endereço não existe ou o documento foi excluído.</p>
        <Link href="/biblioteca" className={`${buttonClasses("secondary", "sm")} mt-4`}>
          Voltar para a Biblioteca
        </Link>
      </EmptyState>
    </div>
  );
}
