import { api } from './api.js';
import { escapeHtml, labels } from './ui.js';

const charts = new Map();
const palette = ['#a98aff', '#76a7ff', '#62d9e8', '#6bd7a4', '#f4bd66', '#f27989'];

function replaceChart(id, emptyId, type, items, labelMap) {
  const canvas = document.getElementById(id);
  const empty = document.getElementById(emptyId);
  if (charts.has(id)) charts.get(id).destroy();
  if (!items?.length || !window.Chart) {
    canvas.hidden = true;
    empty.hidden = false;
    return;
  }
  canvas.hidden = false;
  empty.hidden = true;
  const text = getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim();
  const config = type === 'doughnut'
    ? { type, data: { labels: items.map((item) => labelMap[item.key] || item.key), datasets: [{ data: items.map((item) => item.count), backgroundColor: palette, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--surface').trim(), borderWidth: 4, hoverOffset: 5 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '67%', plugins: { legend: { position: 'bottom', labels: { color: text, usePointStyle: true, pointStyle: 'circle', boxWidth: 7, padding: 13, font: { family: 'DM Sans', size: 10 } } } } } }
    : { type, data: { labels: items.map((item) => new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' }).format(new Date(`${item.date}T12:00:00`))), datasets: [{ label: 'Atendimentos', data: items.map((item) => item.count), borderColor: '#a98aff', backgroundColor: 'rgba(169,138,255,.12)', fill: true, tension: .35, pointRadius: 2, pointHoverRadius: 5 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: text, font: { size: 9 } }, border: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0, color: text, font: { size: 9 } }, grid: { color: 'rgba(150,150,180,.1)' }, border: { display: false } } } } };
  charts.set(id, new window.Chart(canvas, config));
}

function stat(label, value, icon, cls = '') {
  const formatted = typeof value === 'string' ? value : Number(value || 0).toLocaleString('pt-BR');
  return `<article class="stat-card ${cls}"><div class="stat-top"><span>${label}</span><span class="stat-icon"><i data-lucide="${icon}"></i></span></div><div class="stat-value">${escapeHtml(formatted)}</div></article>`;
}

export async function loadAnalytics(days = Number(document.querySelector('#analytics-days').value)) {
  try {
    const [overview, distribution, timeline] = await Promise.all([api.overview(), api.distribution(), api.timeline(days)]);
    document.querySelector('#analytics-stats').innerHTML = [
      stat('Total de atendimentos', overview.total, 'inbox'),
      stat('Revisões humanas', overview.human_review, 'user-round-search', 'accent-amber'),
      stat('Encaminhados', overview.routed, 'send', 'accent-green'),
      stat('Falhas de encaminhamento', overview.routing_failed, 'circle-alert', 'accent-amber'),
      stat('Taxa de encaminhamento', overview.classified ? `${Math.round((overview.routed / overview.classified) * 100)}%` : '—', 'chart-no-axes-combined'),
    ].join('');
    replaceChart('analytics-timeline', 'analytics-timeline-empty', 'line', timeline.items, {});
    replaceChart('analytics-category', 'analytics-category-empty', 'doughnut', distribution.category, labels.category);
    replaceChart('analytics-department', 'analytics-department-empty', 'doughnut', distribution.department, labels.department);
    replaceChart('analytics-priority', 'analytics-priority-empty', 'doughnut', distribution.priority, labels.priority);
    replaceChart('analytics-sentiment', 'analytics-sentiment-empty', 'doughnut', distribution.sentiment, labels.sentiment);
  } catch (error) {
    document.querySelector('#analytics-stats').innerHTML = `<article class="panel"><strong>Não foi possível carregar os dados</strong><p>${escapeHtml(error.message)}</p></article>`;
  } finally {
    window.lucide?.createIcons();
  }
}

export function refreshAnalyticsCharts() {
  if (charts.size) loadAnalytics().catch(() => {});
}
