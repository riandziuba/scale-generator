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

// ---- Stop Server ----
document.getElementById('btn-stop').addEventListener('click', async () => {
  try {
    const res = await fetch('/api/shutdown', { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      toast(t(data.error || 'errorGeneric'), 'error');
      return;
    }
    toast(t('serverStopped'), 'success');
  } catch (e) {
    toast(t('serverStopped'), 'success');
  }
});

// ---- Init ----
document.addEventListener('DOMContentLoaded', () => {
  setLanguage(localStorage.getItem('scale-generator-lang') || 'pt');
  loadAll();
});
