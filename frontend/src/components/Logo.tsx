import { cn } from "@/lib/cn";

/**
 * Símbolo do Cognita: um "C" geométrico (arco aberto à direita) cujas pontas e lado
 * esquerdo são nós de informação, todos ligados a um nó central — conhecimento conectado.
 * O arco usa o Electric Blue; os nós e conexões, o Cyan.
 */
export function LogoMark({ className, title }: { className?: string; title?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("shrink-0", className)}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <g stroke="var(--accent)" strokeWidth="1.4" strokeLinecap="round" opacity="0.85">
        <line x1="16.6" y1="16" x2="22.36" y2="9.64" />
        <line x1="16.6" y1="16" x2="22.36" y2="22.36" />
        <line x1="16.6" y1="16" x2="7" y2="16" />
      </g>
      <path
        d="M22.36 9.64 A9 9 0 1 0 22.36 22.36"
        fill="none"
        stroke="var(--primary)"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      <g fill="var(--accent)">
        <circle cx="22.36" cy="9.64" r="2" />
        <circle cx="22.36" cy="22.36" r="2" />
        <circle cx="7" cy="16" r="2" />
        <circle cx="16.6" cy="16" r="2.3" />
      </g>
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark className="size-8" />
      <span className="font-display text-lg leading-none font-semibold tracking-tight text-text">
        Cognita <span className="text-primary">AI</span>
      </span>
    </span>
  );
}
