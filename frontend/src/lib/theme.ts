export type ThemePreference = "light" | "dark" | "system";

export const THEME_STORAGE_KEY = "cognita-theme";

/**
 * Script executado no <head>, ANTES de a página aparecer, para aplicar o tema salvo.
 * Sem ele, quem usa o tema escuro veria um "flash" branco a cada carregamento.
 */
export const themeScript = `(function(){
  var d = document.documentElement, pref = "system";
  try { pref = localStorage.getItem("${THEME_STORAGE_KEY}") || "system"; } catch (e) {}
  var dark = pref === "dark" || (pref !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  d.dataset.theme = dark ? "dark" : "light";
  d.dataset.themePref = pref;
})();`;

export function resolveTheme(pref: ThemePreference): "light" | "dark" {
  if (pref !== "system") return pref;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyTheme(pref: ThemePreference, animate = true): void {
  const root = document.documentElement;
  if (animate) {
    root.classList.add("theme-transition");
    window.setTimeout(() => root.classList.remove("theme-transition"), 250);
  }
  root.dataset.theme = resolveTheme(pref);
  root.dataset.themePref = pref;
}

export function readPreference(): ThemePreference {
  try {
    const v = localStorage.getItem(THEME_STORAGE_KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

export function savePreference(pref: ThemePreference): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, pref);
  } catch {
    // Navegação privada ou armazenamento bloqueado: o tema vale só nesta sessão.
  }
}
