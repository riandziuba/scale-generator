// ---- Rehearsal Modal ----
async function openRehearsalModal(scaleId) {
  try {
    const list = await API.get('/api/escalas');
    const scale = list.find(e => e.id === scaleId);
    if (!scale) return;

    document.getElementById('input-ensaio-escala-id').value = scaleId;

    const select = document.getElementById('select-ensaio-pessoa');
    select.innerHTML = `<option value="">${t('modalEnsaioSelectResp')}</option>`
      + scale.assignments.map(p =>
        `<option value="${p.id}">${escHtml(p.name)}</option>`
      ).join('');

    if (scale.rehearsal) {
      document.getElementById('input-ensaio-data').value = scale.rehearsal.date;
      document.getElementById('input-ensaio-horario').value = scale.rehearsal.time;
      select.value = scale.rehearsal.person_id || '';
    } else {
      document.getElementById('input-ensaio-data').value = '';
      document.getElementById('input-ensaio-horario').value = '';
      select.value = '';
    }

    document.getElementById('modal-ensaio').style.display = 'flex';
  } catch (e) { toastErr(e); }
}

function closeRehearsalModal() {
  document.getElementById('modal-ensaio').style.display = 'none';
}

document.querySelector('.modal-close').addEventListener('click', closeRehearsalModal);
document.querySelector('.modal-close-btn').addEventListener('click', closeRehearsalModal);
document.getElementById('modal-ensaio').addEventListener('click', (e) => {
  if (e.target === e.currentTarget) closeRehearsalModal();
});

document.getElementById('form-ensaio').addEventListener('submit', async (e) => {
  e.preventDefault();
  const scale_id = parseInt(document.getElementById('input-ensaio-escala-id').value);
  const date = document.getElementById('input-ensaio-data').value;
  const time = document.getElementById('input-ensaio-horario').value;
  const person_id = parseInt(document.getElementById('select-ensaio-pessoa').value);

  if (!date || !time || !person_id) {
    toast(t('ensaioFillAll'), 'error');
    return;
  }

  try {
    await API.post('/api/ensaios', { scale_id, date, time, person_id });
    toast(t('ensaioSaved'));
    closeRehearsalModal();
    loadScales();
  } catch (e) { toastErr(e); }
});

// ---- Rehearsal List ----
async function loadRehearsals() {
  try {
    const list = await API.get('/api/ensaios');
    renderRehearsals(list);
  } catch (e) { toastErr(e); }
}

function renderRehearsals(list) {
  const container = document.getElementById('lista-ensaios');

  if (!list.length) {
    container.innerHTML = `<div class="empty-state">${t('ensaioNoConfigs')}</div>`;
    return;
  }

  container.innerHTML = list.map(en => `
    <div class="scale-card">
      <div class="scale-card-header">
        <h3>
          ${t('ensaioLabel')} ${formatDate(en.scale_date)}
          <span class="badge badge-sunday">${formatDate(en.date)} ${t('scalesRehearsalTimeSep')} ${escHtml(en.time)}</span>
        </h3>
        <div class="actions">
          <button class="btn-danger btn-sm" onclick="deleteRehearsal(${en.id})">${t('scalesDelete')}</button>
        </div>
      </div>
      <div class="scale-meta">
        ${t('ensaioResponsible')}: ${en.person_name ? escHtml(en.person_name) : `<em>${t('ensaioNotDefined')}</em>`}
      </div>
    </div>
  `).join('');
}

async function deleteRehearsal(id) {
  if (!confirm(t('confirmDeleteEnsaio'))) return;
  try {
    await API.delete(`/api/ensaios/${id}`);
    toast(t('ensaioDeleted'));
    loadScales();
  } catch (e) { toastErr(e); }
}
