document.addEventListener('click', (event) => {
  if (!(event.target instanceof Element)) return;
  const toggle = event.target.closest('.password-toggle');
  if (!toggle) return;

  const password = document.getElementById(toggle.getAttribute('aria-controls'));
  if (!(password instanceof HTMLInputElement)) return;

  const isVisible = password.type === 'text';
  password.type = isVisible ? 'password' : 'text';
  toggle.textContent = isVisible ? 'Show' : 'Hide';
  toggle.setAttribute('aria-pressed', String(!isVisible));
});

const sessionWelcome = document.getElementById('sessionWelcome');
const logoutButton = document.getElementById('logoutButton');

if (sessionWelcome || logoutButton) {
  fetch('/api/me', { credentials: 'same-origin' })
    .then(async (response) => {
      if (response.status === 401) {
        window.location.assign('/login');
        return null;
      }
      if (!response.ok) throw new Error('Could not load the current user.');
      return response.json();
    })
    .then((user) => {
      if (!user) return;
      if (sessionWelcome) {
        sessionWelcome.textContent = `Welcome back, ${user.username}`;
        sessionWelcome.hidden = false;
      }
      document.body.dataset.role = user.role;
      document.querySelectorAll('.nav-admin').forEach((link) => {
        if (user.role !== 'admin') link.hidden = true;
      });
    })
    .catch(() => {
      window.location.assign('/login');
    });
}

if (logoutButton) {
  logoutButton.addEventListener('click', async () => {
    logoutButton.disabled = true;
    try {
      const response = await fetch('/api/logout', {
        method: 'POST',
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error('Could not log out.');
      window.location.assign('/login?logged_out=1');
    } catch {
      logoutButton.disabled = false;
      logoutButton.textContent = 'Log out failed';
    }
  });
}
