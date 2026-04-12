// LASPAD Event — main.js

// Fermeture automatique des messages flash
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('[data-auto-dismiss]');
  alerts.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Confirmation avant soumission de formulaires dangereux
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
  });

  // Copie dans le presse-papier
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      navigator.clipboard.writeText(btn.dataset.copy).then(() => {
        const original = btn.textContent;
        btn.textContent = 'Copié !';
        setTimeout(() => (btn.textContent = original), 1500);
      });
    });
  });
});
