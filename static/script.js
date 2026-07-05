// ---- Bootstrap ----

// ---- Tabs ----
document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// ---- Language Switcher ----
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
});

async function loadAll() {
  loadPeople();
  loadUnavailability();
  loadScales();
}

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  setLanguage(localStorage.getItem('scale-generator-lang') || 'pt');
  loadAll();
});
