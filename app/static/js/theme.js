/* Calmora: theme toggle and small UI behaviours.
   The initial theme is applied in base.html's <head> before first paint;
   this file handles switching and keeps the server preference in sync. */
(function () {
  const root = document.documentElement;

  function syncIcon(theme) {
    const icon = document.getElementById('themeToggleIcon');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon';
  }

  window.calmoraToggleTheme = function () {
    const next = (root.getAttribute('data-bs-theme') || 'light') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-bs-theme', next);
    try { localStorage.setItem('calmora-theme', next); } catch (e) {}
    syncIcon(next);
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (document.body.dataset.authenticated === 'true') {
      fetch('/auth/theme/toggle', { method: 'POST', headers: { 'X-CSRFToken': csrfToken } }).catch(() => {});
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    syncIcon(root.getAttribute('data-bs-theme') || 'light');

    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('show'));

    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
      setTimeout(() => { const a = bootstrap.Alert.getOrCreateInstance(el); a && a.close(); }, 5000);
    });
  });
})();

