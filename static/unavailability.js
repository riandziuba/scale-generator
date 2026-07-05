// ---- Unavailability ----
async function loadUnavailability() {
  try {
    const data = await API.get('/api/indisponibilidades');
    renderUnavailability(data);
  } catch (e) { toastErr(e); }
}

function renderUnavailability(list) {
  const tbody = document.querySelector('#tabela-indisponibilidades tbody');
  tbody.innerHTML = list.map(i => `
    <tr>
      <td>${escHtml(i.person_name)}</td>
      <td>${formatDate(i.date)}</td>
      <td class="actions">
        <button class="btn-danger btn-sm" onclick="deleteUnavailability(${i.id})">${t('peopleDelete')}</button>
      </td>
    </tr>
  `).join('');
}

async function deleteUnavailability(id) {
  if (!confirm(t('confirmDeleteUnav'))) return;
  try {
    await API.delete(`/api/indisponibilidades/${id}`);
    toast(t('unavRemoved'));
    loadUnavailability();
  } catch (e) { toastErr(e); }
}

document.getElementById('form-indisponibilidade').addEventListener('submit', async (e) => {
  e.preventDefault();
  const person_id = document.getElementById('select-pessoa-indispo').value;
  const date = document.getElementById('input-data-indispo').value;
  if (!person_id || !date) return;
  try {
    await API.post('/api/indisponibilidades', { person_id: parseInt(person_id), date });
    document.getElementById('input-data-indispo').value = '';
    toast(t('unavRegistered'));
    loadUnavailability();
  } catch (e) { toastErr(e); }
});
