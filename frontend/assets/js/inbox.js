import { api } from './api.js';
import { badge, escapeHtml, formatDate, labels, notify, statusClass } from './ui.js';

let currentPage = 1;
let totalPages = 1;
const pageSize = 10;

export async function loadInbox(page = currentPage) {
  currentPage = page;
  const form = document.querySelector('#inbox-filters');
  const params = new URLSearchParams({ page: String(currentPage), page_size: String(pageSize), sort: 'desc' });
  for (const [key, value] of new FormData(form)) if (String(value).trim()) params.set(key, String(value).trim());
  const body = document.querySelector('#inbox-body');
  body.innerHTML = '<tr><td colspan="7"><div class="table-loading"><span class="spinner"></span> Carregando atendimentos...</div></td></tr>';
  try {
    const data = await api.attendances(Object.fromEntries(params));
    totalPages = Math.max(1, Math.ceil(data.total / pageSize));
    document.querySelector('#inbox-count').textContent = `${data.total} atendimento${data.total === 1 ? '' : 's'}`;
    document.querySelector('#page-label').textContent = `${currentPage} / ${totalPages}`;
    document.querySelector('#page-prev').disabled = currentPage <= 1;
    document.querySelector('#page-next').disabled = currentPage >= totalPages;
    if (!data.items.length) {
      body.innerHTML = '<tr><td class="empty-cell" colspan="7"><div class="empty-state"><strong>Nenhum atendimento encontrado</strong><p>Experimente ajustar os filtros ou registrar uma nova mensagem.</p></div></td></tr>';
      return;
    }
    body.innerHTML = data.items.map((item) => {
      const classification = item.classification;
      const priority = classification?.priority || '';
      const priorityClass = priority === 'critical' || priority === 'high' ? 'badge-danger' : priority === 'medium' ? 'badge-warning' : 'badge-info';
      return `<tr><td data-label="Atendimento"><div class="table-main"><strong>${escapeHtml(item.customer_name || 'Cliente')}</strong><small>${escapeHtml(classification?.summary || item.id)}</small></div></td><td data-label="Categoria">${classification ? badge(labels.category[classification.category] || classification.category, 'badge-purple') : '—'}</td><td data-label="Departamento">${classification ? escapeHtml(labels.department[classification.department] || classification.department) : '—'}</td><td data-label="Prioridade">${classification ? badge(labels.priority[priority] || priority, priorityClass) : '—'}</td><td data-label="Status">${badge(labels.status[item.status] || item.status, statusClass(item.status))}</td><td data-label="Data">${formatDate(item.created_at)}</td><td data-label="Ações"><button class="table-action" data-attendance-id="${escapeHtml(item.id)}" aria-label="Ver detalhes"><i data-lucide="arrow-up-right"></i></button></td></tr>`;
    }).join('');
    window.lucide?.createIcons();
  } catch (error) {
    body.innerHTML = `<tr><td colspan="7"><div class="empty-state"><strong>Não foi possível carregar a Inbox</strong><p>${escapeHtml(error.message)}</p></div></td></tr>`;
    notify(error.message, 'error');
  }
}

function detailMetric(label, value) {
  return `<div class="detail-cell"><small>${label}</small><strong>${escapeHtml(value ?? '—')}</strong></div>`;
}

export async function openAttendanceDetail(id) {
  const dialog = document.querySelector('#detail-dialog');
  const content = document.querySelector('#detail-content');
  content.innerHTML = '<div class="table-loading"><span class="spinner"></span> Carregando detalhes...</div>';
  if (!dialog.open) dialog.showModal();
  try {
    const item = await api.attendance(id);
    const classification = item.classification;
    const routing = item.routing;
    const review = classification?.requires_human_review;
    const priority = classification?.priority;
    const priorityClass = priority === 'critical' || priority === 'high' ? 'badge-danger' : priority === 'medium' ? 'badge-warning' : 'badge-info';
    content.innerHTML = `<div class="detail-head"><div><span class="panel-kicker">DETALHES DO ATENDIMENTO</span><h2 id="detail-title">${escapeHtml(item.customer_name || 'Cliente')}</h2><p class="result-id">ID ${escapeHtml(item.id)}</p></div><button class="icon-button" data-close-dialog aria-label="Fechar"><i data-lucide="x"></i></button></div>
      <div class="detail-body">
        <div class="detail-grid">${detailMetric('Status', labels.status[item.status] || item.status)}${detailMetric('Origem', item.source)}${detailMetric('Criado em', formatDate(item.created_at))}${detailMetric('E-mail', item.customer_email || 'Não informado')}</div>
        <div class="detail-block"><h3>Mensagem original</h3><p>${escapeHtml(item.original_message)}</p></div>
        ${classification ? `<div class="detail-grid">${detailMetric('Categoria', labels.category[classification.category] || classification.category)}${detailMetric('Departamento', labels.department[classification.department] || classification.department)}${detailMetric('Prioridade', labels.priority[priority] || priority)}${detailMetric('Sentimento', labels.sentiment[classification.sentiment] || classification.sentiment)}${detailMetric('Confiança', `${Math.round(classification.confidence * 100)}%`)}${detailMetric('Encaminhamento', labels.routing[routing?.status] || routing?.status || '—')}</div>
          <div class="detail-block"><h3>Resumo da IA</h3><p>${escapeHtml(classification.summary)}</p></div>
          <div class="detail-block"><h3>Justificativa</h3><p>${escapeHtml(classification.reason)}</p></div>
          ${review ? `<div class="review-callout"><i data-lucide="user-round-search"></i><span>Revisão humana necessária: ${escapeHtml(classification.review_reason || 'A classificação requer conferência.')}</span></div>` : ''}
          ${routing?.error_message ? `<div class="alert alert-error">${escapeHtml(routing.error_message)}</div>` : ''}` : '<div class="detail-block"><h3>Classificação</h3><p>A classificação não está disponível.</p></div>'}
      </div><div class="detail-footer">${routing && ['failed', 'pending'].includes(routing.status) && !review ? `<button class="button button-primary" data-retry-routing="${escapeHtml(item.id)}"><i data-lucide="rotate-cw"></i> Tentar encaminhar novamente</button>` : ''}<button class="button button-subtle" data-close-dialog>Fechar</button></div>`;
    window.lucide?.createIcons();
  } catch (error) {
    content.innerHTML = `<div class="detail-head"><div><h2 id="detail-title">Não foi possível carregar</h2></div><button class="icon-button" data-close-dialog aria-label="Fechar"><i data-lucide="x"></i></button></div><div class="detail-body"><p>${escapeHtml(error.message)}</p></div>`;
    window.lucide?.createIcons();
  }
}

export function getInboxPage() { return { currentPage, totalPages }; }
