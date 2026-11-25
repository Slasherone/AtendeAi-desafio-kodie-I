# Desenvolvimento e execução

Este guia reúne os comandos de desenvolvimento, testes e diagnóstico. Para uma primeira execução, o caminho recomendado é Docker Compose. A aplicação é demonstrativa e não oferece autenticação de usuários finais nem hardening para exposição pública.

## Pré-requisitos

- Docker Desktop ou Docker Engine com Docker Compose.
- Para executar a API fora de containers: Python 3.11 ou superior.
- Para os testes de navegador: Node.js/npm e o Chromium do Playwright.
- Credencial de um serviço de IA compatível com Chat Completions e `response_format: json_schema` estrito para classificar mensagens reais.

## Variáveis de ambiente

Crie `.env` a partir de `.env.example` e preencha os valores necessários. O `.env` está ignorado pelo Git; não o compartilhe nem o versione.

| Variável | Finalidade |
|---|---|
| `APP_ENV` | Campo de configuração declarado; não altera comportamento da aplicação nesta versão. |
| `APP_HOST` | Campo declarado; o Compose define o host do container como `0.0.0.0` e o comando local do Uvicorn usa seus padrões. |
| `APP_PORT` | Porta publicada no host pelo Compose; o container da API escuta em `8000`. A execução local do Uvicorn usa `8000` por padrão. |
| `DATABASE_URL` | URL do SQLite. O padrão salva em `data/atendeai.db`. |
| `AI_PROVIDER` | Identificador do modo compatível configurado (`openai_compatible`). |
| `AI_API_KEY` | Credencial do provedor de IA. |
| `AI_BASE_URL` | Raiz do endpoint compatível com OpenAI; o serviço acrescenta `/chat/completions`. |
| `AI_MODEL` | Identificador do modelo configurado. O exemplo usa Gemini via endpoint OpenAI-compatible. |
| `AI_TIMEOUT` | Limite total, em segundos, da chamada e retries de IA. |
| `AI_MAX_RETRIES` | Retries para respostas transitórias; de `0` a `3`. |
| `AI_CONFIDENCE_THRESHOLD` | Abaixo desse valor, a API exige revisão humana; padrão `0.70`. |
| `N8N_WEBHOOK_URL` | URL do webhook. O Compose usa `http://n8n:5678/webhook/atendeai/route` como padrão quando não preenchida. |
| `N8N_API_TOKEN` | Token que autentica a chamada da API ao webhook. |
| `N8N_TIMEOUT` | Timeout das chamadas ao n8n. |
| `INTERNAL_API_TOKEN` | Token exigido pelo callback interno da API. |
| `FRONTEND_URL` | Campo de configuração declarado; não é consumido pelo código da aplicação nesta versão. |

Além das variáveis listadas no `.env.example`, o Compose aceita `N8N_PORT`, `N8N_HOST`, `N8N_WEBHOOK_BASE_URL` e `GENERIC_TIMEZONE`, definidos em `docker-compose.yml` com valores padrão. Não inclua credenciais reais em exemplos ou documentação.

Revise as políticas de privacidade e retenção do provedor antes de enviar dados. Para desenvolvimento, prefira mensagens sintéticas e não envie informações pessoais ou confidenciais sem autorização.

## Docker Compose

No PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# Edite .env: configure AI_API_KEY e os tokens do n8n/API.
docker compose up --build
```

Endereços padrão:

- Aplicação, frontend e API: `http://localhost:8000`
- Interface do n8n: `http://localhost:5678`
- Documentação interativa da API: `http://localhost:8000/docs`

O SQLite fica em `./data` e os dados de configuração do n8n ficam no volume `n8n_data`. Não use `localhost` para comunicação entre containers: a API acessa o n8n pelo nome de serviço `n8n`, e o callback do n8n acessa a API por `http://api:8000`.

Depois de configurar e publicar o workflow, siga [`WORKFLOW_N8N.md`](WORKFLOW_N8N.md) para verificar a integração.

## Execução local da API

No PowerShell, usando Python 3.11 ou superior:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edite `.env` para preencher `AI_API_KEY` e `AI_MODEL`, e inicie a API:

```powershell
uvicorn app.main:app --reload
```

A API serve também os arquivos do frontend. Se `N8N_WEBHOOK_URL` não estiver configurada, a classificação ainda pode ser persistida, mas o encaminhamento permanecerá pendente. Para encaminhar, disponibilize um n8n alcançável pela API, configure o webhook e os tokens e siga o guia do workflow. A configuração padrão de endereços entre containers aplica-se ao Compose; não funciona automaticamente para processos locais fora da rede Docker.

### macOS e Linux

O fluxo local equivalente usa uma virtualenv e não sobrescreve um `.env` existente:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
uvicorn app.main:app --reload
```

## Testes

### Backend

Com as dependências instaladas:

```powershell
python -m pytest -q
python -m compileall -q app tests scripts
```

Os testes Python usam SQLite temporário e doubles/mocks para integrações; não fazem chamadas pagas à IA nem ao n8n.

### Navegador

Com a aplicação acessível, instale as dependências e o Chromium e execute a suíte. O Playwright usa `http://127.0.0.1:8001` como URL padrão; configure `ATENDEAI_BASE_URL` se estiver usando outra porta.

```powershell
npm.cmd --prefix tests/e2e install
tests\e2e\node_modules\.bin\playwright.cmd install chromium
$env:ATENDEAI_BASE_URL = "http://127.0.0.1:8000"
npm.cmd --prefix tests/e2e test
```

A suíte cobre Chromium desktop e viewport móvel; respostas da API são mockadas, portanto esses testes não comprovam chamadas reais à IA ou ao n8n.

Em macOS/Linux, os comandos equivalentes são:

```bash
npm --prefix tests/e2e install
tests/e2e/node_modules/.bin/playwright install chromium
ATENDEAI_BASE_URL=http://127.0.0.1:8000 npm --prefix tests/e2e test
```

### Capturas reais do frontend

O script consulta a API real e cancela a captura se houver qualquer atendimento no banco. Ele preserva imagens existentes.

```powershell
$env:ATENDEAI_BASE_URL = "http://127.0.0.1:8000"
npm.cmd --prefix tests/e2e run capture:ui
```

Use somente um banco vazio e dados seguros. O script captura telas vazias; as capturas de resultado e detalhes exigem uma execução demonstrativa separada com mensagem sintética.

## Sondas de integração

Teste direto do provedor de IA (usa uma mensagem sintética padrão e faz uma tentativa por padrão; pode consumir cota do provedor):

```powershell
python -m scripts.check_ai_connection
```

Teste do workflow ativo no Compose:

```powershell
docker compose exec -T api python -m scripts.check_n8n_webhook
```

A sonda n8n usa um ID inexistente e espera alcançar o callback autenticado sem criar registros. Nenhuma dessas sondas substitui o teste completo pela interface.

Para validar o arquivo Compose sem imprimir configurações ou variáveis de ambiente, use:

```powershell
docker compose config --quiet
```
