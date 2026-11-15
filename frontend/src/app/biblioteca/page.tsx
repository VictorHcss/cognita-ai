import { Library } from "@/components/library/Library";

export default function BibliotecaPage() {
  return (
    <div className="max-w-6xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Biblioteca</h1>
        <p className="mt-1 text-neutral-500">
          Envie documentos, organize em coleções e confira o texto extraído.
        </p>
      </header>
      <Library />
    </div>
  );
}
