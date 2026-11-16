import { MessagesSquare } from "lucide-react";
import type { Metadata } from "next";
import { AskPanel } from "@/components/chat/AskPanel";
import { PageHeader } from "@/components/ui";

export const metadata: Metadata = { title: "Chat" };

export default function ChatPage() {
  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        title="Chat"
        icon={MessagesSquare}
        description="Pergunte aos seus documentos. As respostas usam apenas o conteúdo da biblioteca e citam as fontes — clique em um número para ver o trecho."
      />
      <AskPanel />
    </div>
  );
}
