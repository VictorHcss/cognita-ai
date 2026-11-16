# Fundação de design (entre as Etapas 4 e 5)

## Conceito estudado
**Design system com tokens semânticos**: em vez de espalhar cores pelo código ("azul",
"cinza-500"), cada cor tem um **papel** (`surface`, `muted`, `link`). Os temas apenas
redefinem os valores dos papéis.

## Problema que resolve
Antes, cada tela repetia classes e cores próprias (`text-neutral-500`, `dark:bg-...`).
Trocar a identidade visual ou adicionar um tema exigiria editar todas as telas.
Agora: uma mudança em `globals.css` atualiza o produto inteiro.

## Decisões
- **Tokens como variáveis CSS + Tailwind v4 (`@theme inline`)**: geram classes como
  `bg-surface` e `text-muted` que leem a variável do tema atual.
- **Tema via `data-theme` no `<html>`**, aplicado por um script inline no `<head>` antes
  da renderização — evita o "flash" do tema errado.
- **Preferência em `localStorage`**: é uma conveniência do navegador (não precisa ir ao banco).
- **Componentes base** (`Button`, `Card`, `Badge`...) para as próximas telas (Chat,
  Laboratórios) nascerem consistentes.
- **Contraste medido, não estimado** (ver abaixo).

## O cálculo de contraste (WCAG)
Luminância relativa de uma cor sRGB: cada canal `c` (0–1) vira
`c/12.92` se `c ≤ 0.03928`, senão `((c+0.055)/1.055)^2.4`;
`L = 0.2126·R + 0.7152·G + 0.0722·B`.
Contraste = `(L_clara + 0.05) / (L_escura + 0.05)`. **AA para texto normal: ≥ 4,5.**

### O que a medição revelou
A primeira versão foi feita com contas "de cabeça" e parecia boa. Ao medir os 42 pares
(7 cores de texto × 3 fundos × 2 temas), **9 falhavam** — principalmente as cores de status
no tema claro (verde de "Processado" tinha 3,86:1). Os tons foram escurecidos/clareados
mantendo o matiz até todos passarem (menor contraste final: 4,73:1).

| Caso | Antes | Depois |
|---|---|---|
| Branco sobre Electric Blue (botão) | 4,05 | 4,83 (botão usa `#2F6AE8`) |
| Steel Gray no fundo claro | 2,95 | 5,35 (`#5B6779`) |
| Verde "Processado" (claro) sobre `surface-2` | 3,86 | 4,73 |

## Problemas encontrados nos testes
- **Tabela da Biblioteca transbordava** em telas de ~1000 px (rolagem horizontal da página
  inteira e nomes cortados em "tem…"). Causa: lista de coleções ao lado da tabela deixava
  ~400 px para 7 colunas. Correção: coleções ao lado só a partir de 1280 px, coluna
  "Enviado" só em telas largas, e a tabela rola dentro do próprio card se precisar.
- **Capturas "congeladas" no meio de animações** no painel de testes: não era bug — o painel
  em segundo plano só conclui animações CSS quando redesenha. Confirmado lendo o estado
  da animação (`finished`, opacidade 1).

## Testes realizados
- Lint e tipos sem erros; build de produção ok.
- 8 telas sem rolagem horizontal em 375 px, 5 em 768 px e desktop.
- Troca de tema, persistência após recarregar e modo Sistema.
- Menu em gaveta no celular (abre, fecha, Esc).

## Possíveis melhorias
- Gráficos com a paleta da marca nos Laboratórios (Etapas 7 e 8).
- Testes visuais automatizados (capturas comparadas) quando a interface estabilizar.
