/* MiGaraje: tema claro/oscuro independiente de app.js.
   Mantiene la preferencia en este navegador sin tocar la sesión ni los datos. */
(() => {
  'use strict';

  const STORAGE_KEY = 'migaraje_theme';
  const root = document.documentElement;

  function readPreference() {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'dark' ? 'dark' : 'light';
    } catch {
      return 'light';
    }
  }

  function savePreference(value) {
    try { localStorage.setItem(STORAGE_KEY, value); }
    catch { /* El cambio seguirá funcionando durante esta visita. */ }
  }

  function syncControls() {
    const dark = root.dataset.theme === 'dark';
    const label = dark ? 'Activar modo claro' : 'Activar modo oscuro';

    document.querySelectorAll('.theme-toggle').forEach(button => {
      button.setAttribute('aria-label', label);
      button.setAttribute('title', label);
      button.setAttribute('aria-pressed', String(dark));
    });

    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute('content', dark ? '#0b1425' : '#087df5');
  }

  function setTheme(theme, persist = true) {
    root.dataset.theme = theme === 'dark' ? 'dark' : 'light';

    if (persist) savePreference(root.dataset.theme);

    syncControls();
  }

  // Se ejecuta desde <head> antes de cargar el CSS
  // para evitar el destello blanco.
  root.dataset.theme = readPreference();

  document.addEventListener('DOMContentLoaded', () => {
    syncControls();

    document.querySelectorAll('.theme-toggle').forEach(button => {
      button.addEventListener('click', () => {
        setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
      });
    });
  });
})();
