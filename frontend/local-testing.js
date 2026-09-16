// Prevent test forms from submitting to production services.
document.addEventListener('submit', function (event) {
  event.preventDefault();
  alert('Local frontend test: form submissions require the original backend.');
}, true);
