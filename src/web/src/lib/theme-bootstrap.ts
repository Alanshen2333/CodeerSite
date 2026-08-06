import { THEME_MEDIA_QUERY, THEME_STORAGE_KEY } from "@/lib/theme";

export const themeBootstrapScript = `
(function() {
  var stored = null;
  try { stored = localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)}); } catch (e) {}
  var theme = stored === "light" || stored === "dark"
    ? stored
    : (window.matchMedia(${JSON.stringify(THEME_MEDIA_QUERY)}).matches ? "dark" : "light");
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
})();
`;
