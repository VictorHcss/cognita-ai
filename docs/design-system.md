# Design system — Cognita AI

> Plataforma de inteligência artificial com aparência de laboratório profissional de
> pesquisa e engenharia de conhecimento.

**Personalidade:** tecnologia, conhecimento, precisão, confiança, inovação.
**Evitar:** gradientes em excesso, cores saturadas, efeitos futuristas exagerados,
aparência genérica de chatbot.

## Paleta da marca

| Nome | Hex | Uso |
|---|---|---|
| Midnight Navy | `#101827` | Fundo do tema escuro; texto do tema claro |
| Deep Slate | `#17243A` | Superfícies e painéis (escuro) |
| Electric Blue | `#3978F6` | Marca, destaques, foco, item ativo |
| Cyan | `#39C6D6` | Conexões e "inteligência": similaridade, embeddings, nós do logo |
| Cloud White | `#E8EDF5` | Texto do tema escuro |
| Steel Gray | `#8492A6` | Texto secundário (escuro) |

## Tokens semânticos

As telas **nunca** usam hex direto — só tokens (em `frontend/src/app/globals.css`), para que
claro e escuro troquem tudo de uma vez:

| Token | Classe Tailwind | Claro | Escuro |
|---|---|---|---|
| `--bg` | `bg-bg` | `#F5F7FB` | `#101827` |
| `--surface` | `bg-surface` | `#FFFFFF` | `#17243A` |
| `--surface-2` | `bg-surface-2` | `#EEF2F8` | `#1D2C45` |
| `--border` | `border-border` | `#DDE3EC` | `#25344E` |
| `--text` | `text-text` | `#101827` | `#E8EDF5` |
| `--muted` | `text-muted` | `#5B6779` | `#8B98AB` |
| `--primary` | `text-primary` / `bg-primary` | `#3978F6` | `#3978F6` |
| `--primary-fill` | `bg-primary-fill` (botões) | `#2F6AE8` | `#2F6AE8` |
| `--link` | `text-link` | `#2A5FD6` | `#6A9AF9` |
| `--accent` | `bg-accent` | `#39C6D6` | `#39C6D6` |
| `--accent-text` | `text-accent-text` | `#0D7582` | `#39C6D6` |
| `--success` / `--warning` / `--danger` | `text-success`… | `#1B7A51` / `#9C5B00` / `#C4363E` | `#3FB68B` / `#E5A93B` / `#F16D74` |

### Acessibilidade (contraste WCAG AA)
Todos os 42 pares texto × fundo (7 cores de texto × 3 fundos × 2 temas) têm contraste
**≥ 4,5:1** (menor: 4,73). Para isso, alguns tons foram ajustados **sem mudar a marca**:

- **Botões** usam `#2F6AE8` em vez do Electric Blue: branco sobre `#3978F6` dá 4,05:1
  (abaixo do mínimo); sobre `#2F6AE8`, 4,83:1. O Electric Blue continua em ícones,
  indicadores, foco e no logo.
- **Steel Gray no tema claro** dá só 2,95:1 → usamos `#5B6779`.
- **Links** no escuro usam o azul clareado `#6A9AF9` (6,4:1 sobre o navy).
- **Cyan como texto** no claro vira `#0D7582`; como preenchimento (barras, nós) segue `#39C6D6`.

Para conferir depois de mudar uma cor, o cálculo está descrito em
`docs/aprendizado/05-fundacao-de-design.md`.

## Tipografia

| Fonte | Uso |
|---|---|
| **Space Grotesk** | Títulos (`h1`–`h3`), números de indicadores (`font-display`) |
| **Inter** | Textos, menus, botões, tabelas (`font-sans`) |
| Monoespaçada do sistema | IDs, modelos, offsets, pontuações (`font-mono`) |

Números em tabelas e indicadores usam `tabular-nums` (alinhados).

## Logotipo

Um **"C" geométrico** (arco aberto à direita, Electric Blue) cujas pontas e lado esquerdo
são **nós de informação** (Cyan) ligados a um **nó central** — conhecimento conectado.

- Componente: `frontend/src/components/Logo.tsx` (`<Logo />` com nome, `<LogoMark />` só o símbolo).
- Ícone da aplicação: `frontend/src/app/icon.svg` (símbolo sobre quadrado navy arredondado).
- Usa os tokens `--primary` e `--accent`, então se adapta aos temas.

## Componentes (`frontend/src/components/ui/`)

| Componente | Para quê |
|---|---|
| `Button` / `buttonClasses()` | Ações. Variantes `primary`, `secondary`, `ghost`, `danger`; tamanhos `sm`, `md` |
| `Card`, `CardHeader` | Painéis com borda sutil |
| `Badge` | Status e metadados. Tons `neutral`, `info`, `accent`, `success`, `warning`, `danger` |
| `fieldClasses` | Campos de texto e seleção |
| `PageHeader` | Título + ícone + descrição de cada página |
| `EmptyState` | Telas vazias com ícone e orientação |
| `Stat` | Indicadores (KPIs) da visão geral |
| `Alert` | Erros e avisos |

Ícones: **Lucide** (`lucide-react`), tamanho 16 px (`size-4`) no texto e 20 px em destaques.

## Convenções de cor por significado

- **Azul (primary):** navegação, ação principal, item selecionado.
- **Cyan (accent):** tudo que é "inteligência" — similaridade, modelo de embedding, upload
  para a base de conhecimento.
- **Verde/âmbar/vermelho:** apenas status (processado / processando / falhou).

## Temas

- **Claro, Escuro e Sistema**, escolhidos no rodapé da sidebar.
- A preferência é salva no navegador (`localStorage`, chave `cognita-theme`).
- Um script no `<head>` aplica o tema **antes** da página aparecer (sem "flash" branco).
- No modo Sistema, o tema acompanha o sistema operacional em tempo real.

## Layout e movimento

- Sidebar fixa de 256 px no desktop; no celular vira barra superior + gaveta (fecha com Esc).
- Conteúdo com largura máxima de 1152 px.
- Cantos: `rounded-lg` (campos, botões) e `rounded-xl` (cards).
- Animações curtas (≤ 250 ms): entrada das páginas, troca de tema, hover. Respeitam
  `prefers-reduced-motion`.
- Testado sem rolagem horizontal em 375 px (celular), 768 px (tablet) e desktop.
