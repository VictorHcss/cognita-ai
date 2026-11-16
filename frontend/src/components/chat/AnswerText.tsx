import { Fragment } from "react";

const CITATION = /\[(\d+(?:\s*[,;]\s*\d+)*)\]/g;

function renderBold(text: string, keyPrefix: string) {
  // Suporte mínimo a **negrito**, que os modelos usam com frequência.
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={`${keyPrefix}-${i}`} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <Fragment key={`${keyPrefix}-${i}`}>{part}</Fragment>
    ),
  );
}

/** Texto da resposta com as citações [n] transformadas em botões que levam à fonte. */
export function AnswerText({
  text,
  validNumbers,
  onCite,
}: {
  text: string;
  validNumbers: Set<number>;
  onCite: (n: number) => void;
}) {
  const nodes: React.ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const start = match.index ?? 0;
    nodes.push(...renderBold(text.slice(last, start), `t${start}`));
    const numbers = match[1].split(/[,;]/).map((n) => Number(n.trim()));
    nodes.push(
      <span key={`c${start}`} className="mx-0.5 inline-flex gap-0.5 align-baseline">
        {numbers.map((n) =>
          validNumbers.has(n) ? (
            <button
              key={n}
              type="button"
              onClick={() => onCite(n)}
              aria-label={`Ir para a fonte ${n}`}
              className="rounded bg-accent-soft px-1.5 font-mono text-xs leading-5 font-medium text-accent-text transition hover:bg-accent hover:text-white"
            >
              {n}
            </button>
          ) : (
            <span
              key={n}
              title="Fonte inexistente — a resposta citou um número que não está na lista"
              className="rounded bg-danger/12 px-1.5 font-mono text-xs leading-5 text-danger line-through"
            >
              {n}
            </span>
          ),
        )}
      </span>,
    );
    last = start + match[0].length;
  }
  nodes.push(...renderBold(text.slice(last), "fim"));
  return <p className="text-[15px] leading-7 whitespace-pre-wrap text-text">{nodes}</p>;
}
