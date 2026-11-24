import { api } from './api.js';
import { setServiceRows } from './ui.js';

export async function loadSettings() {
  try {
    const services = await api.services();
    setServiceRows(document.querySelector('#settings-services'), services);
  } catch {
    setServiceRows(document.querySelector('#settings-services'), { api: 'unavailable', ai: 'unavailable', n8n: 'unavailable' });
  }
}
