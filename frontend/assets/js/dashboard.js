import { api } from './api.js';
import { badge, escapeHtml, formatDate, labels, setServiceRows, statusClass } from './ui.js';

const chartRefs = new Map();
const colors = ['#a98aff', '#76a7ff', '#62d9e8', '#6bd7a4', '#f4bd66', '#f27989'];

function chartTextColor() {
  return getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim();
}

function emptyOrChart(id, emptyId, config, hasData) {
  const canvas = document.getElementById(id);
  const empty = document.getElementById(emptyId);
  if (chartRefs.has(id)) chartRefs.get(id).destroy();
  if (!hasData || !window.Chart) {
    canvas.hidden = true;
    empty.hidden = false;
    return;
  }
  canvas.hidden = false;
  empty.hidden = true;
  chartRefs.set(id, new window.Chart(canvas, config));
}

function countStat(label, value, icon, accent, hint) {
  return `<article class="stat-card ${accent}"><div class="stat-top"><span>${label}</span><span class="stat-icon"><i data-lucide="${icon}"></i></span></div><div class="stat-value">${Number(value || 0).toLocaleString('pt-BR')}</div><div class="stat-hint">${hint}</div></article>`;
}

function renderDistributionChart(canvasId, emptyId, items, labelMap) {
  emptyOrChart(canvasId, emptyId, {
    type: 'doughnut',
    data: { labels: items.map((item) => labelMap[item.key] || item.key), datasets: [{ data: items.map((item) => item.count), backgroundColor: colors, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--surface').trim(), borderWidth: 4, hoverOffset: 5 }] },
    options: { responsive: true, maintainAspectRatio: false, cutout: '69%', plugins: { legend: { position: 'bottom', labels: { color: chartTextColor(), usePointStyle: true, pointStyle: 'circle', boxWidth: 7, padding: 14, font: { family: 'DM Sans', size: 10 } } } } },
  }, items.some((item) => item.count > 0));
}

function renderTimeline(items) {
  const hasData = items.some((item) => item.count > 0);
  emptyOrChart('overview-timeline', 'timeline-empty', {
    type: 'line',
    data: { labels: items.map((item) => new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' }).format(new Date(`${item.date}T12:00:00`))), datasets: [{ label: 'Atendimentos', data: items.map((item) => item.count), borderColor: '#a98aff', backgroundColor: 'rgba(169,138,255,.12)', fill: true, tension: .36, pointRadius: 3, pointHoverRadius: 5, pointBackgroundColor: '#a98aff' }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: chartTextColor(), font: { size: 9 } }, border: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0, color: chartTextColor(), font: { size: 9 } }, grid: { color: 'rgba(150,150,180,.1)' }, border: { display: false } } } },
  }, hasData);
}

export async function loadDashboard() {
  const stats = document.querySelector('#overview-stats');
  try {
    const [overview, distribution, timeline, recent, services] = await Promise.all([
      api.overview(), api.distribution(), api.timeline(14), api.attendances({ page: 1, page_size: 5 }), api.services(),
    ]);
    stats.innerHTML = [
      countStat('Total de atendimentos', overview.total, 'inbox', '', '<strong>mensagens registradas</strong>'),
      countStat('Classificados', overview.classified, 'scan-search', 'accent-blue', '<strong>com análise concluída</strong>'),
      countStat('Aguardando encaminhamento', overview.pending_routing, 'clock-3', 'accent-amber', '<strong>pendentes no n8n</strong>'),
      countStat('Encaminhados', overview.routed, 'send', 'accent-green', '<strong>destino registrado</strong>'),
      countStat('Revisão humana', overview.human_review, 'user-round-search', 'accent-amber', '<strong>atenção necessária</strong>'),
    ].join('');
    renderDistributionChart('overview-category', 'category-empty', distribution.category || [], labels.category);
    renderDistributionChart('overview-department', 'department-empty', distribution.department || [], labels.department);
    renderDistributionChart('overview-priority', 'priority-empty', distribution.priority || [], labels.priority);
    renderTimeline(timeline.items || []);
    const recentList = document.querySelector('#recent-list');
    recentList.innerHTML = recent.items.length ? recent.items.map((item) => {
      const summary = item.classification?.summary || item.id;
      return `<div class="recent-row" data-attendance-id="${escapeHtml(item.id)}"><span class="recent-title">${escapeHtml(item.customer_name || 'Cliente')}</span>${badge(labels.status[item.status] || item.status, statusClass(item.status))}<span class="recent-subtitle">${escapeHtml(summary)} · ${formatDate(item.created_at)}</span></div>`;
    }).join('') : '<div class="empty-state"><strong>Nenhum atendimento ainda</strong><p>Crie o primeiro atendimento para começar.</p></div>';
    setServiceRows(document.querySelector('#service-status'), services);
  } catch (error) {
    stats.innerHTML = '<div class="empty-state"><strong>Não foi possível carregar os indicadores</strong><p>Verifique se a API está disponível e atualize a página.</p></div>';
    document.querySelector('#recent-list').innerHTML = '';
    setServiceRows(document.querySelector('#service-status'), { api: 'unavailable', ai: 'unavailable', n8n: 'unavailable' });
    throw error;
  } finally {
    window.lucide?.createIcons();
  }
}

export function refreshDashboardCharts() {
  if (chartRefs.size) loadDashboard().catch(() => {});
}
