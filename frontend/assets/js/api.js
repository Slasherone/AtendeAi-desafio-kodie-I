const API_TIMEOUT_MS = 180000;

export async function apiRequest(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeout ?? API_TIMEOUT_MS);
  try {
    const response = await fetch(path, {
      ...options,
      signal: controller.signal,
      headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
    });
    const raw = await response.text();
    let payload = null;
    if (raw) {
      try { payload = JSON.parse(raw); } catch { payload = { detail: raw }; }
    }
    if (!response.ok) {
      const detail = payload?.detail;
      const message = typeof detail === 'string' ? detail : detail?.message || `Não foi possível concluir a solicitação (${response.status}).`;
      const error = new Error(message);
      error.status = response.status;
      error.data = payload;
      throw error;
    }
    return payload;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('A solicitação demorou demais. Verifique o estado do atendimento antes de tentar novamente.');
    if (error instanceof TypeError) throw new Error('Não foi possível conectar à API do AtendeAI.');
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export const api = {
  health: () => apiRequest('/health'),
  services: () => apiRequest('/api/v1/services/health'),
  overview: () => apiRequest('/api/v1/analytics/overview'),
  distribution: () => apiRequest('/api/v1/analytics/distribution'),
  timeline: (days = 14) => apiRequest(`/api/v1/analytics/timeline?days=${days}`),
  attendances: (params = {}) => apiRequest(`/api/v1/attendances?${new URLSearchParams(params)}`),
  attendance: (id) => apiRequest(`/api/v1/attendances/${encodeURIComponent(id)}`),
  createAttendance: (data) => apiRequest('/api/v1/attendances', { method: 'POST', body: JSON.stringify(data) }),
  retryRouting: (id) => apiRequest(`/api/v1/attendances/${encodeURIComponent(id)}/dispatch`, { method: 'POST' }),
};
