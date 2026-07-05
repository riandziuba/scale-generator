// ---- Reports ----
function buildReportHtml(scales) {
  const dataAtual = new Date().toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US');
  let itemsHtml = '';

  for (const e of scales) {
    const tipoLabel = e.type === 'sunday' ? t('scalesSunday') : t('scalesExtra');
    const peopleHtml = e.assignments.length
      ? e.assignments.map(p => `<span>${escHtml(p.name)}</span>`).join('')
      : `<em>${t('scalesNoOne')}</em>`;

    const rehearsalHtml = e.rehearsal
      ? `<div class="report-ensaio">${t('scalesRehearsalLabel')} ${formatDate(e.rehearsal.date)} ${t('scalesRehearsalTimeSep')} ${escHtml(e.rehearsal.time)}${e.rehearsal.person_name ? ` — ${t('ensaioResponsible')}: ${escHtml(e.rehearsal.person_name)}` : ''}</div>`
      : '';

    const descHtml = e.description ? ` — ${escHtml(e.description)}` : '';

    itemsHtml += `
      <div class="report-scale">
        <h3>${tipoLabel} — ${formatDate(e.date)}${descHtml}</h3>
        <div class="report-people">${peopleHtml}</div>
        ${rehearsalHtml}
      </div>`;
  }

  const totalPeople = scales.reduce((s, e) => s + e.assignments.length, 0);

  return `
    <div class="report-card">
      <div class="report-header">
        <h2>${t('reportDocTitle')}</h2>
        <p>${t('reportGeneratedIn')} ${dataAtual}</p>
        <p>${scales.length} ${t('reportScales')} · ${totalPeople} ${t('reportPeople')}</p>
      </div>
      ${itemsHtml}
      <div class="report-footer">${t('reportFooter')}</div>
    </div>`;
}

document.getElementById('btn-relatorio-pdf').addEventListener('click', async () => {
  try {
    const scales = await API.get('/api/escalas');
    if (!scales.length) {
      toast(t('reportNoData'), 'error');
      return;
    }
    const html = buildReportHtml(scales);
    const printEl = document.getElementById('relatorio-print');
    printEl.innerHTML = html + `<div class="report-actions"><button class="btn-primary" onclick="window.print()">${t('reportPrint')}</button></div>`;
    printEl.style.display = 'block';
    toast(t('reportGenerated'));
  } catch (e) { toastErr(e); }
});

document.getElementById('btn-relatorio-png').addEventListener('click', async () => {
  try {
    const scales = await API.get('/api/escalas');
    if (!scales.length) {
      toast(t('reportNoData'), 'error');
      return;
    }

    const html = buildReportHtml(scales);
    const container = document.getElementById('relatorio-container');
    container.innerHTML = html + `<div class="report-actions"><button class="btn-primary" id="btn-download-png">${t('reportDownloadPng')}</button></div>`;

    const el = container.querySelector('.report-card');

    if (typeof html2canvas === 'undefined') {
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      await new Promise((resolve, reject) => {
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }

    const canvas = await html2canvas(el, {
      scale: 2,
      backgroundColor: '#ffffff',
      useCORS: true,
      logging: false,
    });

    const link = document.createElement('a');
    link.download = 'relatorio-escala.png';
    link.href = canvas.toDataURL('image/png');
    link.click();
    toast(t('reportPngDownloaded'));
  } catch (e) { toastErr(e); }
});
