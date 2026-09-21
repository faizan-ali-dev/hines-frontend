// Prevent test forms from submitting to production services.
document.addEventListener('submit', function (event) {
  if (event.target.matches('[data-auth-form]')) return;
  event.preventDefault();
  alert('Local frontend test: form submissions require the original backend.');
}, true);
