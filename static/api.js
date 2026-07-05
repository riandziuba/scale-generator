// ---- Shared helpers ----

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return '';
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

function toast(msg, type = 'success') {
  const el = document.getElementById('toast') || (() => {
    const t = document.createElement('div');
    t.id = 'toast';
    document.body.appendChild(t);
    return t;
  })();
  el.textContent = msg;
  el.className = type;
  el.classList.add('show');
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove('show'), 3000);
}

function toastErr(err) {
  console.error(err);
  toast(err.message || t('errorGeneric'), 'error');
}

function translateError(j) {
  if (!j || !j.error) return t('errorGeneric');
  return j.error.startsWith('error_') ? t(j.error) : j.error;
}

const API = {
  async get(url) {
    const r = await fetch(url);
    if (!r.ok) {
      let msg = t('errorGeneric');
      try { msg = translateError(await r.json()); } catch (_) {}
      throw new Error(msg);
    }
    return r.json();
  },
  async post(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      let msg = t('errorGeneric');
      try { msg = translateError(await r.json()); } catch (_) {}
      throw new Error(msg);
    }
    return r.json();
  },
  async delete(url) {
    const r = await fetch(url, { method: 'DELETE' });
    if (!r.ok) {
      let msg = t('errorDelete');
      try { msg = translateError(await r.json()); } catch (_) {}
      throw new Error(msg);
    }
  },
  async put(url, body) {
    const r = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      let msg = t('errorGeneric');
      try { msg = translateError(await r.json()); } catch (_) {}
      throw new Error(msg);
    }
    return r.json();
  },
};
