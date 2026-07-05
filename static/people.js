// ---- People ----
let people = [];

async function loadPeople() {
  try {
    people = await API.get('/api/pessoas');
    renderPeople();
    renderPersonSelect();
  } catch (e) { toastErr(e); }
}

function renderPeople() {
  const tbody = document.querySelector('#tabela-pessoas tbody');
  tbody.innerHTML = people.map(p => `
    <tr>
      <td>${escHtml(p.name)}</td>
      <td>${escHtml(p.contact)}</td>
      <td class="actions">
        <button class="btn-danger btn-sm" onclick="deletePerson(${p.id})">${t('peopleDelete')}</button>
      </td>
    </tr>
  `).join('');
}

function renderPersonSelect() {
  const selects = document.querySelectorAll('#select-pessoa-indispo, #select-ensaio-pessoa');
  selects.forEach(sel => {
    const current = sel.value;
    const placeholderKey = sel.id === 'select-ensaio-pessoa' ? 'modalEnsaioSelectResp' : 'unavSelect';
    sel.innerHTML = `<option value="">${t(placeholderKey)}</option>`
      + people.map(p => `<option value="${p.id}">${escHtml(p.name)}</option>`).join('');
    sel.value = current;
  });
}

async function deletePerson(id) {
  if (!confirm(t('confirmDeletePerson'))) return;
  try {
    await API.delete(`/api/pessoas/${id}`);
    toast(t('personDeleted'));
    loadPeople();
    loadUnavailability();
  } catch (e) { toastErr(e); }
}

document.getElementById('form-pessoa').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('input-nome').value.trim();
  const contact = document.getElementById('input-contato').value.trim();
  if (!name) return;
  try {
    await API.post('/api/pessoas', { name, contact });
    document.getElementById('input-nome').value = '';
    document.getElementById('input-contato').value = '';
    toast(t('personRegistered'));
    loadPeople();
  } catch (e) { toastErr(e); }
});
