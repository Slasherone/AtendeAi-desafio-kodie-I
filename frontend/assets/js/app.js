import { api } from './api.js';
import { loadDashboard } from './dashboard.js';
import { loadInbox, openAttendanceDetail, getInboxPage } from './inbox.js';
import { loadAnalytics } from './analytics.js';
import { loadSettings } from './settings.js';
import { badge, escapeHtml, formatDate, labels, notify, statusClass } from './ui.js';

const viewLabels = Object.fromEntries([...document.querySelectorAll('.view')].map((view) => [view.id.replace('view-', ''), view.dataset.title]));
let loadedViews = new Set();

function applyTheme(choice) {
  const resolved = choice === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : choice;
  document.documentElement.dataset.theme = resolved;
  localStorage.setItem('atendeai-theme-choice', choice);
  const icon = document.querySelector('#theme-toggle i');
  icon?.setAttribute('data-lucide', resolved === 'dark' ? 'sun' : 'moon');
  document.querySelector('#theme-toggle').setAttribute('aria-label', resolved === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro');
  document.querySelectorAll('[data-theme-choice]').forEach((button) => button.classList.toggle('active', button.dataset.themeChoice === choice));
  window.lucide?.createIcons();
  for (const view of ['overview', 'analytics']) {
    if (loadedViews.has(view)) {
      loadedViews.delete(view);
      if (document.querySelector(`#view-${view}`).classList.contains('active')) {
        const refresh = view === 'overview' ? loadDashboard : loadAnalytics;
        refresh().catch(() => {});
        loadedViews.add(view);
      }
    }
  }
}

function initTheme() {
  applyTheme(localStorage.getItem('atendeai-theme-choice') || 'system');
  document.querySelector('#theme-toggle').addEventListener('click', () => {
    const current = document.documentElement.dataset.theme;
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });
  document.querySelectorAll('[data-theme-choice]').forEach((button) => button.addEventListener('click', () => applyTheme(button.dataset.themeChoice)));
  matchMedia('(prefers-color-scheme: light)').addEventListener?.('change', () => {
    if (localStorage.getItem('atendeai-theme-choice') === 'system') applyTheme('system');
  });
}

async function navigate(viewName, updateHash = true) {
  const name = viewLabels[viewName] ? viewName : 'overview';
  document.querySelectorAll('.view').forEach((view) => view.classList.toggle('active', view.id === `view-${name}`));
  document.querySelectorAll('.nav-item[data-view]').forEach((button) => button.classList.toggle('active', button.dataset.view === name));
  document.querySelector('#page-breadcrumb').textContent = viewLabels[name];
  document.querySelector('#sidebar').classList.remove('open');
  if (updateHash) history.replaceState(null, '', `#${name}`);
  if (!loadedViews.has(name) || name === 'inbox') {
    if (name === 'overview') await loadDashboard().catch((error) => notify(error.message, 'error'));
    if (name === 'inbox') await loadInbox(1);
    if (name === 'analytics') await loadAnalytics();
    if (name === 'settings') await loadSettings();
    loadedViews.add(name);
  }
  window.lucide?.createIcons();
}

function renderClassificationResult(result) {
  const item = result.classification;
  const route = result.routing;
  if (!item) return '';
  const priorityClass = ['critical', 'high'].includes(item.priority) ? 'badge-danger' : item.priority === 'medium' ? 'badge-warning' : 'badge-info';
  const review = item.requires_human_review;
  const status = labels.status[result.status] || result.status;
  return `<article class="result-card"><div class="result-head"><div><span class="panel-kicker">ANÁLISE CONCLUÍDA</span><h2>Resultado da classificação</h2><p>${escapeHtml(status)} · ${formatDate(result.created_at)}</p></div>${badge(review ? 'Revisão necessária' : labels.routing[route?.status] || 'Classificado', review ? 'badge-warning' : statusClass(route?.status || result.status))}</div>
    ${review ? `<div class="review-callout"><i data-lucide="user-round-search"></i><span>${escapeHtml(item.review_reason || 'Este atendimento precisa de revisão humana antes do encaminhamento automático.')}</span></div>` : ''}
    <div class="result-grid"><div class="result-metric"><small>Categoria</small><strong>${badge(labels.category[item.category] || item.category, 'badge-purple')}</strong></div><div class="result-metric"><small>Departamento</small><strong>${escapeHtml(labels.department[item.department] || item.department)}</strong></div><div class="result-metric"><small>Prioridade</small><strong>${badge(labels.priority[item.priority] || item.priority, priorityClass)}</strong></div><div class="result-metric"><small>Sentimento</small><strong>${escapeHtml(labels.sentiment[item.sentiment] || item.sentiment)}</strong></div><div class="result-metric"><small>Confiança estimada</small><strong>${Math.round(item.confidence * 100)}%</strong></div><div class="result-metric"><small>Encaminhamento</small><strong>${escapeHtml(labels.routing[route?.status] || route?.status || 'Pendente')}</strong></div></div>
    <div class="result-summary"><span class="panel-kicker">RESUMO</span><p>${escapeHtml(item.summary)}</p><span class="panel-kicker" style="display:block;margin-top:13px">JUSTIFICATIVA</span><p>${escapeHtml(item.reason)}</p></div><div class="result-footer"><span class="result-id">ID ${escapeHtml(result.id)}</span><button class="text-button" data-view-attendance="${escapeHtml(result.id)}">Ver detalhes <i data-lucide="arrow-up-right"></i></button></div></article>`;
}

function setupForm() {
  const form = document.querySelector('#attendance-form');
  const textarea = form.elements.message;
  textarea.addEventListener('input', () => { document.querySelector('#message-count').textContent = `${textarea.value.length} / 10000`; });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = document.querySelector('#submit-attendance');
    const errorBox = document.querySelector('#form-error');
    const resultBox = document.querySelector('#classification-result');
    errorBox.hidden = true;
    resultBox.replaceChildren();
    if (!form.reportValidity()) return;
    const data = Object.fromEntries(new FormData(form));
    data.message = data.message.trim();
    for (const key of ['customer_name', 'customer_email']) if (!String(data[key] || '').trim()) delete data[key];
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span> Analisando mensagem...';
    try {
      const response = await api.createAttendance(data);
      resultBox.innerHTML = renderClassificationResult(response);
      window.lucide?.createIcons();
      loadedViews.delete('overview');
      loadedViews.delete('inbox');
      loadedViews.delete('analytics');
      notify(response.status === 'routed' ? 'Atendimento classificado e encaminhado.' : 'Classificação concluída. Confira o status do atendimento.');
    } catch (error) {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      notify(error.message, 'error');
    } finally {
      button.disabled = false;
      button.innerHTML = '<i data-lucide="sparkles"></i> Analisar atendimento';
      window.lucide?.createIcons();
    }
  });
}

function setupNavigation() {
  document.querySelectorAll('.nav-item[data-view]').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.view)));
  document.querySelectorAll('[data-go]').forEach((button) => button.addEventListener('click', () => navigate(button.dataset.go)));
  document.querySelector('#menu-toggle').addEventListener('click', () => document.querySelector('#sidebar').classList.toggle('open'));
  document.addEventListener('click', (event) => {
    const sidebar = document.querySelector('#sidebar');
    if (sidebar.classList.contains('open') && !sidebar.contains(event.target) && !event.target.closest('#menu-toggle')) sidebar.classList.remove('open');
  });
  window.addEventListener('hashchange', () => navigate(location.hash.slice(1), false));
  document.querySelector('#today-label').textContent = new Intl.DateTimeFormat('pt-BR', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }).format(new Date());
}

function setupInbox() {
  document.querySelector('#inbox-filters').addEventListener('submit', (event) => { event.preventDefault(); loadInbox(1); });
  document.querySelector('#page-prev').addEventListener('click', () => { const { currentPage } = getInboxPage(); loadInbox(currentPage - 1); });
  document.querySelector('#page-next').addEventListener('click', () => { const { currentPage } = getInboxPage(); loadInbox(currentPage + 1); });
}

function setupDialogActions() {
  const dialog = document.querySelector('#detail-dialog');
  dialog.addEventListener('click', async (event) => {
    const close = event.target.closest('[data-close-dialog]');
    if (close) { dialog.close(); return; }
    const retry = event.target.closest('[data-retry-routing]');
    if (retry) {
      retry.disabled = true;
      retry.textContent = 'Tentando encaminhar...';
      try {
        const result = await api.retryRouting(retry.dataset.retryRouting);
        notify(result.status === 'routed' ? 'Encaminhamento concluído.' : 'Tentativa registrada; verifique o status.');
        await openAttendanceDetail(retry.dataset.retryRouting);
        loadedViews.delete('inbox');
        loadedViews.delete('overview');
      } catch (error) {
        notify(error.message, 'error');
        retry.disabled = false;
        retry.textContent = 'Tentar encaminhar novamente';
      }
    }
  });
  dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  document.addEventListener('click', (event) => {
    const trigger = event.target.closest('[data-attendance-id]');
    if (trigger) openAttendanceDetail(trigger.dataset.attendanceId);
    const result = event.target.closest('[data-view-attendance]');
    if (result) openAttendanceDetail(result.dataset.viewAttendance);
  });
}

async function checkApi() {
  const indicator = document.querySelector('#api-indicator');
  try {
    await api.health();
    indicator.classList.add('service-online');
    indicator.title = 'API disponível';
  } catch {
    indicator.classList.add('service-offline');
    indicator.title = 'API indisponível';
  }
}

function setupAnalytics() {
  document.querySelector('#analytics-days').addEventListener('change', (event) => loadAnalytics(Number(event.target.value)));
}

initTheme();
setupNavigation();
setupForm();
setupInbox();
setupDialogActions();
setupAnalytics();
checkApi();
window.lucide?.createIcons();
navigate(location.hash.slice(1) || 'overview', false);
