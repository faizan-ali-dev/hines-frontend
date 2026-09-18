(function () {
  const storageKey = 'hinesClientProfile';
  const getProfile = () => {
    try { return JSON.parse(localStorage.getItem(storageKey)); } catch { return null; }
  };
  const setMessage = (form, message) => { form.querySelector('.auth-message').textContent = message; };
  const initials = (name) => name.trim().split(/\s+/).slice(0, 2).map(part => part[0] || '').join('').toUpperCase();

  const signUpForm = document.querySelector('[data-signup-form]');
  if (signUpForm) {
    signUpForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const name = signUpForm.fullName.value.trim();
      const email = signUpForm.email.value.trim().toLowerCase();
      const referral = signUpForm.referralCode.value.trim();
      const password = signUpForm.password.value;
      if (!name || !email || !referral || password.length < 8) {
        setMessage(signUpForm, 'Complete every field. Passwords must contain at least 8 characters.');
        return;
      }
      localStorage.setItem(storageKey, JSON.stringify({ name, email, referral, password, username: email }));
      window.location.assign('../dashboard/index.html');
    });
  }

  const loginForm = document.querySelector('[data-login-form]');
  if (loginForm) {
    loginForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const profile = getProfile();
      const username = loginForm.username.value.trim().toLowerCase();
      if (!profile || username !== profile.username || loginForm.password.value !== profile.password) {
        setMessage(loginForm, 'The username or password is incorrect. Create an account first if you are new.');
        return;
      }
      window.location.assign('../dashboard/index.html');
    });
  }

  const dashboard = document.querySelector('[data-dashboard]');
  if (!dashboard) return;
  const profile = getProfile();
  if (!profile) { window.location.replace('../client-login/index.html'); return; }
  document.querySelector('[data-profile-initials]').textContent = initials(profile.name);
  document.querySelector('[data-profile-name]').textContent = profile.name;
  document.querySelector('[data-profile-email]').textContent = profile.email;
  document.querySelector('[data-profile-referral]').textContent = profile.referral;
  document.querySelector('[data-dashboard-name]').textContent = profile.name.split(/\s+/)[0];
  const menu = document.querySelector('.profile-menu');
  const trigger = document.querySelector('[data-profile-trigger]');
  trigger.addEventListener('click', () => {
    const open = menu.classList.toggle('is-open');
    trigger.setAttribute('aria-expanded', String(open));
  });
  document.addEventListener('click', (event) => { if (!menu.contains(event.target)) { menu.classList.remove('is-open'); trigger.setAttribute('aria-expanded', 'false'); } });
  document.querySelector('[data-logout]').addEventListener('click', () => { localStorage.removeItem(storageKey); window.location.assign('../client-login/index.html'); });
})();
