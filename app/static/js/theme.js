/* Calmora - theme toggle
   Applies data-bs-theme to <html> and persists preference server-side
   via /auth/theme/toggle, falling back to localStorage for guests. */
(function () {
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-bs-theme', theme);
    const icon = document.getElementById('themeToggleIcon');
    if (icon) {
      icon.className = theme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
  }

  window.calmoraToggleTheme = function () {
    const current = root.getAttribute('data-bs-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    applyTheme(next);
    localStorage.setItem('calmora-theme', next);

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    if (document.body.dataset.authenticated === 'true') {
      fetch('/auth/theme/toggle', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken }
      }).catch(() => {});
    }
  };

  document.addEventListener('DOMContentLoaded', function () {
    const serverTheme = document.body.dataset.themePref;
    const stored = localStorage.getItem('calmora-theme');
    applyTheme(serverTheme || stored || 'light');

    // mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
      sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    }

    // auto-dismiss flash messages
    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
      setTimeout(() => { const a = bootstrap.Alert.getOrCreateInstance(el); a && a.close(); }, 5000);
    });
  });
})();
