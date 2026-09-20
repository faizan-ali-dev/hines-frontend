document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('[data-profile-menu]');
  const toggle = document.querySelector('[data-profile-toggle]');
  if (!menu || !toggle) return;
  toggle.addEventListener('click', () => {
    const isOpen = menu.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
  });
  document.addEventListener('click', (event) => {
    if (!menu.contains(event.target)) {
      menu.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
});
