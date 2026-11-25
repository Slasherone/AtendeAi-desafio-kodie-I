import { access, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, devices } from '@playwright/test';

const baseURL = process.env.ATENDEAI_BASE_URL || 'http://127.0.0.1:8001';
const outputDirectory = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../docs/screenshots/frontend');

async function exists(filePath) {
  try {
    await access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function saveScreenshot(page, filename) {
  const filePath = path.join(outputDirectory, filename);
  if (await exists(filePath)) {
    console.log(`Mantida captura existente: ${filename}`);
    return;
  }
  await page.screenshot({ path: filePath, fullPage: true, animations: 'disabled' });
  console.log(`Captura real salva: ${filename}`);
}

async function openView(page, view) {
  if (await page.getByRole('button', { name: 'Abrir navegação' }).isVisible()) {
    const sidebar = page.locator('#sidebar');
    if (!(await sidebar.evaluate((element) => element.classList.contains('open')))) {
      await page.getByRole('button', { name: 'Abrir navegação' }).click();
    }
  }
  await page.locator(`#sidebar .nav-item[data-view="${view}"]`).click();
  await page.locator(`#view-${view}.active`).waitFor();
}

const request = await (await import('@playwright/test')).request.newContext({ baseURL });
const listResponse = await request.get('/api/v1/attendances?page=1&page_size=1');
if (!listResponse.ok()) throw new Error(`API indisponível (${listResponse.status()}); inicie o AtendeAI antes de capturar.`);
const list = await listResponse.json();
if (list.total !== 0) {
  throw new Error(`A captura foi cancelada: o banco contém ${list.total} atendimento(s). Para evitar expor dados, use um ambiente vazio.`);
}
await request.dispose();

await mkdir(outputDirectory, { recursive: true });
const browser = await chromium.launch({ headless: true });

try {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await desktop.goto(baseURL, { waitUntil: 'domcontentloaded' });
  await desktop.locator('#recent-list .empty-state').waitFor();
  await openView(desktop, 'new');
  await desktop.locator('#attendance-form').waitFor();
  await saveScreenshot(desktop, 'new-attendance.png');

  await openView(desktop, 'inbox');
  await desktop.locator('#inbox-body .empty-state').waitFor();
  await saveScreenshot(desktop, 'inbox.png');

  await openView(desktop, 'analytics');
  await desktop.locator('#analytics-stats .stat-card').first().waitFor();
  await saveScreenshot(desktop, 'analytics.png');

  await openView(desktop, 'settings');
  await desktop.locator('#settings-services .service-row').first().waitFor();
  await desktop.locator('[data-theme-choice="dark"]').click();
  await saveScreenshot(desktop, 'settings-dark.png');
  await desktop.locator('[data-theme-choice="light"]').click();
  await saveScreenshot(desktop, 'settings-light.png');
  await desktop.close();

  const { defaultBrowserType, ...mobileDevice } = devices['iPhone 13'];
  const mobile = await browser.newPage(mobileDevice);
  await mobile.goto(baseURL, { waitUntil: 'domcontentloaded' });
  await mobile.locator('#recent-list .empty-state').waitFor();
  await saveScreenshot(mobile, 'mobile-dashboard.png');
  await openView(mobile, 'inbox');
  await mobile.locator('#inbox-body .empty-state').waitFor();
  await saveScreenshot(mobile, 'mobile-inbox.png');
  await mobile.close();
} finally {
  await browser.close();
}
