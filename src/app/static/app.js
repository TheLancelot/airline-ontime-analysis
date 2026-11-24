window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.password-toggle').forEach((toggle) => {
    toggle.addEventListener('click', () => {
      const password = document.getElementById(toggle.getAttribute('aria-controls'));
      const isVisible = password.type === 'text';
      password.type = isVisible ? 'password' : 'text';
      toggle.textContent = isVisible ? 'Show' : 'Hide';
      toggle.setAttribute('aria-pressed', String(!isVisible));
    });
  });
});
