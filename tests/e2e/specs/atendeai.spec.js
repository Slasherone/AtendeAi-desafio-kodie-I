import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const attendanceId = 'e2e-attendance-0001';
const createdAt = '2026-11-25T12:00:00Z';
const classification = {
  id: 'e2e-classification-0001',
  category: 'complaint',
  department: 'support',
  priority: 'high',
  sentiment: 'negative',
  summary: 'Cliente relata falha ao acessar a conta.',
  confidence: 0.95,
  requires_human_review: false,
  reason: 'A mensagem descreve um problema de acesso.',
  review_reason: null,
  model_name: 'fixture-model',
  prompt_version: '1.0',
};
const failedAttendance = {
  id: attendanceId,
  customer_name: 'Cliente de teste',
  customer_email: 'teste@example.com',
  source: 'web',
  status: 'routing_failed',
  created_at: createdAt,
  updated_at: createdAt,
  original_message: 'Não consigo acessar minha conta.',
  classification,
  routing: {
    id: 'e2e-routing-0001',
    department: 'support',
    status: 'failed',
    execution_id: null,
    error_message: 'Falha de teste no encaminhamento.',
    attempts: 1,
    created_at: createdAt,
    updated_at: createdAt,
    completed_at: null,
  },
};

function json(route, body, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function installApiMocks(page, { records = [], createDelayMs = 0, createStatus = 201 } = {}) {
  const requests = [];
  let currentDetail = failedAttendance;
  await page.route('**/health', (route) => json(route, { status: 'ok', service: 'AtendeAI API' }));
  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    requests.push({ method: request.method(), path, search: url.search, body: request.postDataJSON?.() });

    if (path.endsWith('/services/health')) {
      return json(route, { api: 'ok', ai: 'configured', n8n: 'ok' });
    }
    if (path.endsWith('/analytics/overview')) {
      return json(route, {
        total: records.length,
        classified: records.length,
        pending_routing: 0,
        routed: records.filter((item) => item.status === 'routed').length,
        human_review: 0,
        routing_failed: records.filter((item) => item.status === 'routing_failed').length,
      });
    }
    if (path.endsWith('/analytics/distribution')) {
      return json(route, {
        category: records.length ? [{ key: 'complaint', count: records.length }] : [],
        department: records.length ? [{ key: 'support', count: records.length }] : [],
        priority: records.length ? [{ key: 'high', count: records.length }] : [],
        sentiment: records.length ? [{ key: 'negative', count: records.length }] : [],
      });
    }
    if (path.endsWith('/analytics/timeline')) {
      return json(route, { items: [{ date: '2026-11-25', count: records.length }] });
    }
    if (path.endsWith('/attendances') && request.method() === 'POST') {
      if (createDelayMs) await new Promise((resolve) => setTimeout(resolve, createDelayMs));
      if (createStatus >= 400) {
        return json(route, { detail: { message: 'Serviço de classificação temporariamente indisponível.' } }, createStatus);
      }
      return json(route, {
        id: 'e2e-created-0001',
        status: 'routed',
        message: 'Classificação concluída; encaminhamento registrado.',
        classification,
        routing: { ...failedAttendance.routing, status: 'completed', error_message: null },
        created_at: createdAt,
      }, 201);
    }
    if (path.endsWith('/attendances') && request.method() === 'GET') {
      const pageNumber = Number(url.searchParams.get('page') || 1);
      const pageSize = Number(url.searchParams.get('page_size') || 20);
      return json(route, {
        items: records.slice((pageNumber - 1) * pageSize, pageNumber * pageSize),
        total: records.length,
        page: pageNumber,
        page_size: pageSize,
      });
    }
    if (path.endsWith(`/attendances/${attendanceId}/dispatch`) && request.method() === 'POST') {
      currentDetail = {
        ...failedAttendance,
        status: 'routed',
        routing: { ...failedAttendance.routing, status: 'completed', error_message: null },
      };
      return json(route, {
        id: attendanceId,
        status: 'routed',
        message: 'Nova tentativa de encaminhamento concluída.',
        classification,
        routing: currentDetail.routing,
        created_at: createdAt,
      });
    }
    if (path.endsWith(`/attendances/${attendanceId}`) && request.method() === 'GET') {
      return json(route, currentDetail);
    }
    return json(route, { detail: `Rota não simulada no teste: ${request.method()} ${path}` }, 404);
  });
  return requests;
}

async function openView(page, label) {
  const menuToggle = page.getByRole('button', { name: 'Abrir navegação' });
  if (await menuToggle.isVisible()) {
    const sidebar = page.locator('#sidebar');
    if (!(await sidebar.evaluate((element) => element.classList.contains('open')))) await menuToggle.click();
  }
  const viewNames = {
    'Visão geral': 'overview',
    'Novo atendimento': 'new',
    Inbox: 'inbox',
    Analytics: 'analytics',
    Configurações: 'settings',
  };
  await page.locator(`#sidebar .nav-item[data-view="${viewNames[label]}"]`).click();
  await expect(page.locator('.view.active h1')).toContainText(label);
}

test.beforeEach(async ({ page }) => {
  await installApiMocks(page);
  page.on('pageerror', (error) => {
    throw error;
  });
});

test('navega pelas áreas principais e carrega os seus estados vazios', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Visão geral/ })).toBeVisible();
  await expect(page.locator('#recent-list')).toContainText('Nenhum atendimento ainda');

  await openView(page, 'Novo atendimento');
  await openView(page, 'Inbox');
  await expect(page.locator('#inbox-body')).toContainText('Nenhum atendimento encontrado');
  await openView(page, 'Analytics');
  await expect(page.locator('#analytics-timeline-empty')).toBeVisible();
  await openView(page, 'Configurações');
  await expect(page.locator('#settings-services')).toContainText('FastAPI');
});

test('alterna os temas e mantém a preferência após recarregar', async ({ page }) => {
  await page.addInitScript(() => {
    if (!localStorage.getItem('atendeai-theme-choice')) localStorage.setItem('atendeai-theme-choice', 'dark');
  });
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

  await page.getByRole('button', { name: 'Ativar tema claro' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');

  await openView(page, 'Configurações');
  await page.getByRole('button', { name: 'Escuro', exact: true }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.getByRole('button', { name: 'Escuro', exact: true })).toHaveClass(/active/);
});

test('valida o formulário, bloqueia envio duplicado e apresenta o resultado', async ({ page }, testInfo) => {
  const requests = await installApiMocks(page, { createDelayMs: 300 });
  await page.goto('/#new');
  const message = page.locator('#attendance-form textarea[name="message"]');
  const submit = page.locator('#submit-attendance');

  await submit.click();
  await expect(message).toBeFocused();
  await expect(page.locator('#classification-result')).toBeEmpty();

  await message.fill('Não consigo acessar minha conta.');
  await page.locator('#attendance-form input[name="customer_name"]').fill('Pessoa de teste');
  await submit.click();
  await expect(submit).toBeDisabled();
  await expect(page.locator('.result-card')).toBeVisible();
  await expect(page.locator('.result-card')).toContainText('Resultado da classificação');
  await expect(page.locator('.result-card')).toContainText('95%');
  await expect(submit).toBeEnabled();
  // Artifact for local visual review only; the API response is a fixture, not execution evidence.
  await page.screenshot({ path: testInfo.outputPath('classification-result-fixture.png'), fullPage: true });
  expect(requests.filter((request) => request.method === 'POST' && request.path.endsWith('/attendances'))).toHaveLength(1);
});

test('mostra um erro compreensível quando a API rejeita a classificação', async ({ page }) => {
  await installApiMocks(page, { createStatus: 503 });
  await page.goto('/#new');
  await page.locator('#attendance-form textarea[name="message"]').fill('Mensagem sintética para teste.');
  await page.locator('#submit-attendance').click();
  await expect(page.locator('#form-error')).toBeVisible();
  await expect(page.locator('#form-error')).toContainText('temporariamente indisponível');
  await expect(page.locator('.result-card')).toHaveCount(0);
});

test('filtra e pesquisa a Inbox e permite abrir e retentar um encaminhamento', async ({ page }, testInfo) => {
  const requests = await installApiMocks(page, { records: [failedAttendance] });
  await page.goto('/#inbox');
  await expect(page.locator('#inbox-body')).toContainText('Cliente de teste');

  await page.locator('#inbox-filters input[name="search"]').fill('conta');
  await page.locator('#inbox-filters select[name="category"]').selectOption('complaint');
  await page.getByRole('button', { name: 'Filtrar' }).click();
  await expect.poll(() => requests.filter((request) => request.path.endsWith('/attendances') && request.method === 'GET').length).toBeGreaterThan(1);
  const filteredRequest = requests.filter((request) => request.path.endsWith('/attendances') && request.method === 'GET').at(-1);
  expect(filteredRequest.search).toContain('search=conta');
  expect(filteredRequest.search).toContain('category=complaint');

  await page.getByRole('button', { name: 'Ver detalhes' }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog).toContainText('Mensagem original');
  await expect(dialog).toContainText('Não consigo acessar minha conta.');
  // Artifact for local visual review only; the API response is a fixture, not execution evidence.
  await page.screenshot({ path: testInfo.outputPath('attendance-detail-fixture.png'), fullPage: true });
  await dialog.evaluate((element) => { element.scrollTop = element.scrollHeight; });
  await page.getByRole('button', { name: 'Tentar encaminhar novamente' }).click();
  await expect(dialog).toContainText('Concluído');
  expect(requests.some((request) => request.method === 'POST' && request.path.endsWith(`/attendances/${attendanceId}/dispatch`))).toBe(true);

  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
});

test('a Inbox pagina os resultados e desabilita limites de navegação', async ({ page }) => {
  const records = Array.from({ length: 11 }, (_, index) => ({
    ...failedAttendance,
    id: `e2e-attendance-page-${index + 1}`,
    customer_name: `Cliente ${index + 1}`,
  }));
  const requests = await installApiMocks(page, { records });
  await page.goto('/#inbox');
  await expect(page.locator('#inbox-body tr')).toHaveCount(10);
  await expect(page.locator('#page-label')).toHaveText('1 / 2');
  await expect(page.locator('#page-prev')).toBeDisabled();
  await page.locator('#page-next').click();
  await expect(page.locator('#page-label')).toHaveText('2 / 2');
  await expect(page.locator('#inbox-body tr')).toHaveCount(1);
  await expect(page.locator('#page-next')).toBeDisabled();
  expect(requests.some((request) => request.method === 'GET' && request.search.includes('page=2'))).toBe(true);
});

test('Analytics aplica o período selecionado e renderiza os dados', async ({ page }, testInfo) => {
  const requests = await installApiMocks(page, { records: [failedAttendance] });
  await page.goto('/#analytics');
  await expect(page.locator('#analytics-stats')).toContainText('1');
  await page.locator('#analytics-days').selectOption('30');
  await expect.poll(() => requests.some((request) => request.path.endsWith('/analytics/timeline') && request.search.includes('days=30'))).toBe(true);
  await expect(page.locator('#analytics-category-empty')).toBeHidden();
  // Artifact for local visual review only; the API response is a fixture, not execution evidence.
  await page.screenshot({ path: testInfo.outputPath('analytics-fixture.png'), fullPage: true });
});

test('layout não cria overflow horizontal e a navegação móvel abre e fecha', async ({ page }, testInfo) => {
  await page.goto('/');
  const dimensions = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    document: document.documentElement.scrollWidth,
  }));
  expect(dimensions.document).toBeLessThanOrEqual(dimensions.viewport + 1);

  if (testInfo.project.name === 'mobile-chromium') {
    const sidebar = page.locator('#sidebar');
    await expect(page.getByRole('button', { name: 'Abrir navegação' })).toBeVisible();
    await page.getByRole('button', { name: 'Abrir navegação' }).click();
    await expect(sidebar).toHaveClass(/open/);
    await page.getByRole('button', { name: 'Inbox', exact: true }).click();
    await expect(sidebar).not.toHaveClass(/open/);
    await expect(page.locator('.view.active h1')).toContainText('Inbox');
    const mobileDimensions = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      document: document.documentElement.scrollWidth,
    }));
    expect(mobileDimensions.document).toBeLessThanOrEqual(mobileDimensions.viewport + 1);
  }
});

test('respeita a preferência de movimento reduzido', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/');
  const durations = await page.locator('.view.active').evaluate((element) => {
    const style = getComputedStyle(element);
    return style.animationDuration.split(',').map((duration) => Number.parseFloat(duration));
  });
  expect(durations.every((duration) => duration <= 0.01)).toBe(true);
});

test('a navegação por teclado tem foco visível e não foca o menu móvel fechado', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.keyboard.press('Tab');
  const firstFocusable = testInfo.project.name === 'mobile-chromium' ? page.locator('#menu-toggle') : page.locator('.brand');
  await expect(firstFocusable).toBeFocused();
  const outline = await firstFocusable.evaluate((element) => getComputedStyle(element).outlineStyle);
  expect(outline).toBe('solid');

  if (testInfo.project.name === 'mobile-chromium') {
    await expect(page.locator('#sidebar')).toHaveAttribute('inert', '');
    await page.keyboard.press('Tab');
    await expect(page.locator('#theme-toggle')).toBeFocused();
    await page.locator('#menu-toggle').click();
    await expect(page.locator('#menu-toggle')).toHaveAttribute('aria-expanded', 'true');
    await expect(page.locator('#sidebar')).not.toHaveAttribute('inert', '');
    await expect(page.locator('#sidebar .nav-item[data-view="overview"]')).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(page.locator('#menu-toggle')).toHaveAttribute('aria-expanded', 'false');
    await expect(page.locator('#menu-toggle')).toBeFocused();
  }
});

test('não apresenta violações críticas ou sérias de acessibilidade nas telas e temas', async ({ page }) => {
  test.setTimeout(90_000);
  await installApiMocks(page, { records: [failedAttendance] });
  await page.goto('/');
  for (const theme of ['light', 'dark']) {
    await page.evaluate((choice) => {
      document.documentElement.dataset.theme = choice;
      localStorage.setItem('atendeai-theme-choice', choice);
    }, theme);
    const scan = async (view) => {
      const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      const serious = results.violations.filter((violation) => ['critical', 'serious'].includes(violation.impact));
      expect(serious, `${theme}/${view}: ${JSON.stringify(serious.map(({ id, impact, nodes }) => ({ id, impact, count: nodes.length })), null, 2)}`).toHaveLength(0);
    };

    await scan('overview');
    await openView(page, 'Novo atendimento');
    await scan('new');
    await openView(page, 'Inbox');
    await page.getByRole('button', { name: 'Ver detalhes' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await scan('attendance-detail');
    await page.keyboard.press('Escape');
    await openView(page, 'Analytics');
    await scan('analytics');
    await openView(page, 'Configurações');
    await scan('settings');
  }
});
