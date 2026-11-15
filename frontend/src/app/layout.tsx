import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { MODULES } from "@/lib/modules";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cognita AI",
  description: "Conhecimento conectado. Inteligência aplicada.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <div className="flex min-h-screen flex-col md:flex-row">
          <aside className="border-b border-neutral-200 bg-neutral-50 p-4 md:w-60 md:border-r md:border-b-0 dark:border-neutral-800 dark:bg-neutral-950">
            <Link href="/" className="block text-lg font-semibold tracking-tight">
              Cognita<span className="text-indigo-500"> AI</span>
            </Link>
            <nav className="mt-4 flex gap-1 overflow-x-auto md:flex-col">
              {MODULES.map((m) => (
                <Link
                  key={m.href}
                  href={m.href}
                  className="rounded-md px-3 py-2 text-sm whitespace-nowrap text-neutral-700 hover:bg-neutral-200 dark:text-neutral-300 dark:hover:bg-neutral-800"
                >
                  {m.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="flex-1 p-6 md:p-10">{children}</main>
        </div>
      </body>
    </html>
  );
}
