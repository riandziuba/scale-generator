// ---- Scales ----
document.getElementById('form-gerar').addEventListener('submit', async (e) => {
  e.preventDefault();
  const num_people = document.getElementById('input-num-pessoas').value;
  const start_date = document.getElementById('input-data-inicio').value;
  const end_date = document.getElementById('input-data-fim').value;
  if (!start_date || !end_date) return;
  try {
    const result = await API.post('/api/escalas/gerar', { num_people, start_date, end_date });
    toast(result.message || `${result.created} ${t('scalesGenerated')}`);
    loadScales();
  } catch (e) { toastErr(e); }
});

document.getElementById('form-extra').addEventListener('submit', async (e) => {
  e.preventDefault();
  const date = document.getElementById('input-data-extra').value;
  const description = document.getElementById('input-descricao-extra').value.trim();
  const num_people = document.getElementById('input-num-extra').value;
  if (!date || !description) return;
  try {
    await API.post('/api/escalas/extra', { date, description, num_people });
    document.getElementById('input-data-extra').value = '';
    document.getElementById('input-descricao-extra').value = '';
    toast(t('scalesExtraAdded'));
    loadScales();
  } catch (e) { toastErr(e); }
});

async function loadScales() {
  try {
    const list = await API.get('/api/escalas');
    renderScales(list);
    loadRehearsals();
  } catch (e) { toastErr(e); }
}

function renderScales(list) {
  const container = document.getElementById('lista-escalas');

  if (!list.length) {
    container.innerHTML = `<div class="empty-state">${t('scalesNoScales')}</div>`;
    return;
  }

  container.innerHTML = list.map(e => {
    const isSunday = e.type === 'sunday';
    const tipoLabel = isSunday ? t('scalesSunday') : t('scalesExtra');
    const badgeClass = isSunday ? 'badge-sunday' : 'badge-extra';

    const peopleHtml = e.assignments.length
      ? e.assignments.map(p => `<span class="scale-person">${escHtml(p.name)}</span>`).join('')
      : `<span class="scale-person empty">${t('scalesNoOne')}</span>`;

    const rehearsalHtml = e.rehearsal
      ? `<div class="ensaio-info">
          <strong>${t('scalesRehearsalLabel')}</strong> ${formatDate(e.rehearsal.date)} ${t('scalesRehearsalTimeSep')} ${escHtml(e.rehearsal.time)}
          ${e.rehearsal.person_name ? `${t('scalesRehearsalResp')}${escHtml(e.rehearsal.person_name)}` : ''}
        </div>`
      : '';

    const descHtml = e.description ? `<span style="color:#666">— ${escHtml(e.description)}</span>` : '';

    const rehearsalBtnLabel = e.rehearsal ? t('scalesRehearsalEdit') : t('scalesRehearsalConfig');

    return `
      <div class="scale-card">
        <div class="scale-card-header">
          <h3>
            <span class="badge ${badgeClass}">${tipoLabel}</span>
            <span class="date">${formatDate(e.date)}</span>
            ${descHtml}
          </h3>
          <div class="actions">
            <button class="btn-secondary btn-sm" onclick="openRehearsalModal(${e.id})">${rehearsalBtnLabel}</button>
            <button class="btn-secondary btn-sm" onclick="regenerateScale(${e.id})">${t('scalesRescale')}</button>
            <button class="btn-danger btn-sm" onclick="deleteScale(${e.id})">${t('scalesDelete')}</button>
          </div>
        </div>
        <div class="scale-meta">
          ${e.assignments.length}/${e.num_people} ${t('scalesPeople')}
          ${e.assignments.length < e.num_people ? `<span style="color:#ef4444;">${t('scalesNotEnough')}</span>` : ''}
        </div>
        <div class="scale-people">${peopleHtml}</div>
        ${rehearsalHtml}
      </div>
    `;
  }).join('');
}

async function regenerateScale(id) {
  if (!confirm(t('confirmRescale'))) return;
  try {
    await API.post(`/api/escalas/${id}/regenerar`);
    toast(t('scalesRegenerated'));
    loadScales();
  } catch (e) { toastErr(e); }
}

async function deleteScale(id) {
  if (!confirm(t('confirmDeleteScale'))) return;
  try {
    await API.delete(`/api/escalas/${id}`);
    toast(t('scalesDeleted'));
    loadScales();
  } catch (e) { toastErr(e); }
}
