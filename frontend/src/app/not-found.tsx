import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl space-y-3 py-10">
      <p className="text-sm font-medium text-indigo-600">Erro 404</p>
      <h1 className="text-2xl font-semibold tracking-tight">Página não encontrada</h1>
      <p className="text-neutral-500">
        O endereço não existe ou o documento foi excluído.
      </p>
      <Link href="/biblioteca" className="inline-block text-sm text-indigo-600 hover:underline">
        ← Voltar para a Biblioteca
      </Link>
    </div>
  );
}
