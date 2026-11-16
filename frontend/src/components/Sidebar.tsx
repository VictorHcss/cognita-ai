"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/cn";
import { HOME, isAvailable, MODULES } from "@/lib/modules";
import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

const GROUPS = ["Conhecimento", "Laboratórios"] as const;

function NavLink({
  href,
  label,
  icon: Icon,
  active,
  soon,
}: {
  href: string;
  label: string;
  icon: (typeof MODULES)[number]["icon"];
  active: boolean;
  soon?: boolean;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
        active
          ? "bg-primary-soft font-medium text-text"
          : "text-muted hover:bg-surface-2 hover:text-text",
      )}
    >
      {active && (
        <span className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-primary" aria-hidden />
      )}
      <Icon
        className={cn("size-4 shrink-0", active ? "text-primary" : "text-muted group-hover:text-text")}
        aria-hidden
      />
      <span className="flex-1 truncate">{label}</span>
      {soon && (
        <span className="rounded px-1.5 py-0.5 text-[10px] tracking-wide text-muted uppercase ring-1 ring-border">
          em breve
        </span>
      )}
    </Link>
  );
}

function NavContent({ pathname }: { pathname: string }) {
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <div className="flex h-full flex-col">
      <div className="px-5 pt-5 pb-6">
        <Link href="/" aria-label="Cognita AI — visão geral">
          <Logo />
        </Link>
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto px-3" aria-label="Principal">
        <NavLink {...HOME} active={isActive(HOME.href)} />
        {GROUPS.map((group) => (
          <div key={group}>
            <p className="mb-1.5 px-3 text-[11px] font-medium tracking-wider text-muted uppercase">
              {group}
            </p>
            <div className="space-y-0.5">
              {MODULES.filter((m) => m.group === group).map((m) => (
                <NavLink
                  key={m.href}
                  href={m.href}
                  label={m.label}
                  icon={m.icon}
                  active={isActive(m.href)}
                  soon={!isAvailable(m)}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>
      <div className="space-y-3 border-t border-border p-4">
        <ThemeToggle />
        <p className="text-center text-[11px] text-muted">Conhecimento conectado.</p>
      </div>
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  // Fecha o menu móvel ao navegar.
  useEffect(() => setOpen(false), [pathname]);

  // Esc fecha o menu móvel.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      {/* Barra superior (celular) */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-surface/90 px-4 py-3 backdrop-blur md:hidden">
        <Link href="/" aria-label="Cognita AI — visão geral">
          <Logo />
        </Link>
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Abrir menu"
          aria-expanded={open}
          className="rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-text"
        >
          <Menu className="size-5" aria-hidden />
        </button>
      </header>

      {/* Gaveta (celular) */}
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/40 transition-opacity md:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={() => setOpen(false)}
        aria-hidden
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 border-r border-border bg-surface transition-transform duration-200 md:hidden",
          open ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Menu"
        inert={!open}
      >
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Fechar menu"
          className="absolute top-4 right-3 rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-text"
        >
          <X className="size-5" aria-hidden />
        </button>
        <NavContent pathname={pathname} />
      </aside>

      {/* Sidebar fixa (desktop) */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-border bg-surface md:block">
        <NavContent pathname={pathname} />
      </aside>
    </>
  );
}
