export const labels = {
  category: { question: 'Dúvida', complaint: 'Reclamação', request: 'Solicitação', compliment: 'Elogio', other: 'Outro' },
  department: { support: 'Suporte', financial: 'Financeiro', commercial: 'Comercial', customer_service: 'Atendimento' },
  priority: { low: 'Baixa', medium: 'Média', high: 'Alta', critical: 'Crítica' },
  sentiment: { positive: 'Positivo', neutral: 'Neutro', negative: 'Negativo' },
  status: { received: 'Recebido', processing: 'Processando', classified: 'Classificado', pending_review: 'Revisão humana', routing: 'Encaminhando', routed: 'Encaminhado', routing_failed: 'Falha no envio', classification_failed: 'Falha na análise' },
  routing: { pending: 'Pendente', held: 'Em revisão', in_progress: 'Em andamento', completed: 'Concluído', failed: 'Falhou' },
};

export function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

export function formatDate(value, withTime = true) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  return new Intl.DateTimeFormat('pt-BR', withTime ? { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' } : { day: '2-digit', month: 'short', year: 'numeric' }).format(date);
}

export function statusClass(status) {
  if (['routed', 'completed'].includes(status)) return 'badge-success';
  if (['pending_review', 'held', 'pending', 'in_progress'].includes(status)) return 'badge-warning';
  if (['routing_failed', 'failed', 'classification_failed'].includes(status)) return 'badge-danger';
  if (['classified', 'processing', 'routing'].includes(status)) return 'badge-purple';
  return 'badge-info';
}

export function badge(label, className = 'badge-info') {
  return `<span class="badge ${className}">${escapeHtml(label)}</span>`;
}

export function notify(message, kind = 'success') {
  const stack = document.querySelector('#toast-stack');
  const item = document.createElement('div');
  item.className = `toast ${kind === 'error' ? 'error' : ''}`;
  const icon = document.createElement('i');
  icon.setAttribute('data-lucide', kind === 'error' ? 'circle-alert' : 'circle-check');
  const text = document.createElement('span');
  text.textContent = message;
  item.append(icon, text);
  stack.append(item);
  window.lucide?.createIcons();
  setTimeout(() => item.remove(), 4500);
}

export function setServiceRows(container, services) {
  const info = [
    { key: 'api', label: 'FastAPI', icon: 'server' },
    { key: 'ai', label: 'Serviço de IA', icon: 'sparkles' },
    { key: 'n8n', label: 'Automação n8n', icon: 'workflow' },
  ];
  container.innerHTML = info.map(({ key, label, icon }) => {
    const isOk = services?.[key] === 'ok' || services?.[key] === 'configured';
    const state = services?.[key] || 'unavailable';
    const stateLabel = state === 'ok' ? 'Disponível' : state === 'configured' ? 'Configurado' : state === 'not_configured' ? 'Não configurado' : 'Indisponível';
    return `<div class="service-row"><i data-lucide="${icon}"></i><span>${label}</span><small class="service-state ${isOk ? 'ok' : ''}">${stateLabel}</small></div>`;
  }).join('');
  window.lucide?.createIcons();
}
