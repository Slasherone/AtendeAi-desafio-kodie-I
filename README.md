# AtendeAI

**Atendimento mais inteligente, do primeiro contato ao encaminhamento.** AtendeAI recebe mensagens de clientes, classifica categoria, departamento, prioridade e sentimento com uma API de IA configurável, persiste os resultados e demonstra o encaminhamento via n8n.

## Problema e solução

Pequenas equipes recebem dúvidas, reclamações, solicitações e elogios em volume crescente. A triagem manual consome tempo e pode atrasar o direcionamento. O AtendeAI organiza essa etapa: FastAPI valida e orquestra a classificação, SQLite mantém o histórico, n8n registra o departamento de destino e uma interface web acompanha indicadores e atendimentos.

## Tecnologias

- Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2, SQLite e HTTPX.
- API de modelo de linguagem compatível com OpenAI Chat Completions.
- n8n com workflow exportado em JSON.
- HTML5, CSS3, JavaScript ES6+, Chart.js e Lucide Icons.
- Docker, Docker Compose, Pytest e Playwright para testes do navegador.

## Arquitetura e fluxo

```text
Navegador → Frontend → FastAPI → serviço de IA → validação Pydantic
                               ├→ SQLite
                               └→ webhook n8n → callback autenticado FastAPI → SQLite
```

O navegador consome apenas a API pública; chaves e tokens ficam no backend/n8n. A classificação validada é persistida antes da automação. Casos que precisam de revisão humana não são encaminhados automaticamente. Se o n8n falhar, a classificação permanece disponível e o encaminhamento pode ser retentado. O workflow demonstra o registro do departamento no backend, sem inventar integrações com sistemas de terceiros.

Consulte [`docs/architecture.md`](docs/architecture.md) para estados e contratos detalhados.

## Contrato de classificação

```json
{
  "category": "complaint",
  "department": "support",
  "priority": "high",
  "sentiment": "negative",
  "summary": "Cliente relata falha ao acessar a conta.",
  "confidence": 0.94,
  "requires_human_review": false,
  "reason": "A mensagem descreve um problema técnico que exige suporte."
}
```

Enums e campos são validados no backend. Confiança inferior a `AI_CONFIDENCE_THRESHOLD` (padrão `0.70`) força revisão humana. Confiança é uma estimativa do modelo, não garantia estatística.

## Executar localmente

Requer Python 3.11 ou superior. Para manter uma versão isolada do Python só para este projeto, instale o gerenciador `uv` (https://docs.astral.sh/uv/) e rode na pasta do projeto:

```powershell
uv python install 3.11
uv venv --python 3.11 .venv311
.\.venv311\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edite `.env` e informe ao menos `AI_API_KEY` e `AI_MODEL` para classificação real. `AI_BASE_URL` pode apontar para qualquer provedor compatível. Para rodar somente a API/frontend sem IA, os serviços sobem, mas criação de atendimento retorna erro de configuração até que a IA seja configurada.

O `.env.example` usa Gemini via Google AI Studio: `AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/` e `AI_MODEL=gemini-3.5-flash-lite`, um modelo gratuito otimizado para tarefas leves e de alto volume, como extração/classificação. A disponibilidade e os limites gratuitos variam por projeto/modelo; confira os limites ativos no AI Studio. No nível gratuito, o Google pode usar o conteúdo para melhorar produtos — use mensagens sintéticas e não envie dados pessoais ou confidenciais. `AI_TIMEOUT` (padrão 90 s) limita o tempo total da classificação, incluindo tentativas; o frontend aguarda até 180 s para cobrir classificação e encaminhamento.

Falhas temporárias HTTP `429`, `500`, `502`, `503` e `504` são repetidas até `AI_MAX_RETRIES` vezes (padrão 2, máximo 3 retries), com espera exponencial curta e respeito limitado ao `Retry-After` numérico. Use `AI_MAX_RETRIES=0` para desativar tentativas. Erros de autenticação/configuração e timeouts não são repetidos; se a indisponibilidade persistir, a API retorna uma mensagem orientando tentar novamente.

A classificação solicita JSON Schema estrito com enums e valida novamente o resultado com Pydantic. Se a saída for inválida, os logs registram somente a etapa e os nomes/tipos dos campos com erro — nunca a mensagem do cliente nem o conteúdo bruto do provedor.

Para testar a IA diretamente, o script envia uma mensagem ao provedor, valida a resposta com o mesmo schema usado pela aplicação e imprime o resultado em JSON, o modelo e a duração. A chave e a entrada completa não são impressas; como o resumo gerado pode refletir o conteúdo, prefira mensagens sintéticas ou autorizadas. Por padrão, usa uma mensagem sintética e **não faz retries** para evitar chamadas externas inesperadas:

```powershell
python -m scripts.check_ai_connection
```

Passe uma mensagem própria e, opcionalmente, altere o timeout ou autorize retries transitórios:

```powershell
python -m scripts.check_ai_connection --message "Não consigo acessar minha conta."
python -m scripts.check_ai_connection --message "Mensagem sintética" --timeout 45 --max-retries 2
```

`--max-retries 0` (padrão) faz uma única tentativa; valores de 1 a 3 são retries adicionais. `--timeout` aceita de 1 a 180 segundos e não altera o `.env`. No Docker, execute o script dentro do container para usar a configuração dele:

```powershell
docker compose exec -T api python -m scripts.check_ai_connection --message "Mensagem sintética"
```

```powershell
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000`; documentação OpenAPI em `/docs`; health em `/health`.

## Executar com Docker Compose

Requer Docker Desktop ou Docker Engine com Compose. Copie `.env.example` para `.env`, defina credenciais e execute:

```powershell
docker compose up --build
```

- AtendeAI: `http://localhost:8000`
- n8n: `http://localhost:5678`
- SQLite persistido em `./data`; dados n8n persistidos no volume `n8n_data`.
- A rede interna usa `http://api:8000`; não use `localhost` entre containers.

Não use valores vazios/placeholders em ambiente público. Proteja o n8n e use tokens longos e únicos.

## Configurar o workflow n8n

1. Faça login na interface n8n e importe `workflows/atendeai-workflow.json`.
2. Crie e vincule a credencial Header Auth `AtendeAI Webhook Header Auth`: campo **Name** = `X-AtendeAI-Token`; campo **Value** = valor de `N8N_API_TOKEN` do `.env`.
3. No node `Registrar encaminhamento no FastAPI`, selecione a credencial Header Auth interna. Nela, campo **Name** = `Authorization` (somente o nome, sem `:`); campo **Value** = `Bearer <INTERNAL_API_TOKEN>`. **Name é o nome do header HTTP, não o rótulo da credencial.** Não coloque `AtendeAI Internal API Auth` nem `Authorization: Bearer ...` no campo **Name**. O título da credencial aparece separadamente no topo da janela e pode variar; confirme qual credencial está selecionada no node.
4. No node `Registrar encaminhamento no FastAPI`, clique em **fx** para mudar o campo URL para o modo **Expression** e cole a expressão abaixo, sem `=` no início:

   ```text
   {{ 'http://api:8000/api/v1/internal/attendances/' + $json.attendance_id + '/route' }}
   ```

   O JSON exportado deve armazenar esse campo com exatamente um `=` inicial: `={{ 'http://api:8000/api/v1/internal/attendances/' + $json.attendance_id + '/route' }}`. Se aparecer `=={{`, remova o `=` excedente: a URL resolvida ficará com um `=` literal e o HTTP Request falhará com `Invalid URL`. Para outro ambiente, troque `http://api:8000` pelo endereço que o container n8n alcance.
5. No n8n 2, clique em **Publish** para colocar a versão editada em produção (salvar alterações mantém o rascunho separado). O caminho de produção é `/webhook/atendeai/route`; a URL de teste do n8n é diferente.
6. Defina o mesmo token interno no backend e na credencial n8n. O arquivo exportado não contém tokens reais.

Após ativar e associar as credenciais, valide o webhook sem gravar atendimento com `docker compose exec -T api python -m scripts.check_n8n_webhook`. O teste usa um ID UUID inexistente e considera esperado o 404 do callback após provar que ambas as autenticações chegaram ao FastAPI.

Capturas reais do workflow publicado, de uma execução bem-sucedida, das configurações dos nodes e do callback estão organizadas em [`docs/screenshots/README.md`](docs/screenshots/README.md). Os valores de credenciais não são mostrados.

## Conectar o OpenCode ao MCP do n8n

O projeto inclui `opencode.json` para conectar o OpenCode ao MCP remoto local do n8n. Para habilitar:

1. No n8n, abra **Settings → Instance-level MCP**, habilite o acesso e use **Connect → API key** para gerar um token MCP. Esse token é separado de `N8N_API_TOKEN` e `INTERNAL_API_TOKEN`.
2. Em **Workflows enabled**, habilite apenas os workflows que o agente deve acessar (por exemplo, AtendeAI). O acesso a workflows habilitados é compartilhado entre clientes MCP dessa instância.
3. No Windows, crie a variável de ambiente do usuário `N8N_MCP_TOKEN` com o token. Não a coloque no Git nem envie em mensagens.
4. Confirme que o Server URL exibido pelo n8n é `http://localhost:5678/mcp-server/http`; se for diferente, ajuste o campo `url` em `opencode.json`.
5. Feche e reinicie o OpenCode para carregar a configuração e a variável. Verifique a conexão em `/mcps` ou com `opencode mcp list`.

O MCP de instância é o modo indicado para pesquisar, criar e editar workflows com um agente; o node `MCP Server Trigger` serve para expor ferramentas de um workflow específico e é outro caso de uso.

Sem essa configuração, a API salva a classificação, mas a automação pode permanecer pendente ou falhar; veja o status do encaminhamento no atendimento. A disponibilidade da API de IA depende das credenciais/provedor do ambiente.

## Testes

```powershell
python -m pytest -q
```

Os testes usam SQLite temporário e mocks para IA e n8n; não fazem chamadas pagas a serviços externos. Casos de avaliação manual do prompt estão em `prompts/classification_test_cases.json` e cobrem dúvida, reclamação técnica, comercial, financeiro, elogio, ambiguidade, urgência, sentimento negativo sem prioridade alta, prompt injection e mensagem sem sentido.

### Testes do frontend no navegador

Com Node.js instalado e a API/frontend em execução, instale o navegador Playwright uma vez e rode os testes:

```powershell
npm.cmd --prefix tests/e2e install
tests\e2e\node_modules\.bin\playwright.cmd install chromium
npm.cmd --prefix tests/e2e test
```

Os testes cobrem Chromium em desktop e viewport móvel, navegação, formulários, erros, Inbox, retentativa, Analytics, temas, movimento reduzido, overflow responsivo e acessibilidade WCAG com axe-core. As respostas da API são fixtures locais: a suíte não chama IA, n8n nem grava atendimentos. Para usar outra URL, defina `ATENDEAI_BASE_URL`.

Para gerar capturas reais das telas vazias usando a API em execução:

```powershell
npm.cmd --prefix tests/e2e run capture:ui
```

O script exige banco sem atendimentos e aborta se encontrar registros, para não capturar dados existentes. As imagens são gravadas em `docs/screenshots/frontend/`; capturas já existentes não são sobrescritas. Resultado e detalhes de uma execução real também estão registrados em `classification-result.png` e `attendance-details.png`: foram gerados com uma mensagem sintética, sem dados pessoais, e confirmados contra o registro persistido após o encaminhamento pelo n8n. Essa execução real requer uma chamada ao provedor de IA configurado.

## Telas

- Visão geral com métricas persistidas, evolução, distribuição, recentes e configuração dos serviços.
- Novo atendimento com formulário, processamento e resultado detalhado.
- Inbox com busca, filtros, paginação e detalhes.
- Analytics com distribuição e evolução temporal.
- Configurações de tema e informações de integrações.
- Temas claro/escuro, layout responsivo e respeito a `prefers-reduced-motion`.

Os dados são reais da API; estados vazios são apresentados quando não existem atendimentos. As capturas de resultado e detalhes mostram uma classificação sintética real, sem dados pessoais, encaminhada pelo n8n. Consulte [`docs/screenshots/README.md`](docs/screenshots/README.md) para a descrição e o estado das evidências visuais.

## Estrutura principal

```text
app/                 API, schemas, modelos, serviços e banco
frontend/            HTML, CSS e módulos JavaScript
prompts/              Prompt e casos para avaliação manual
workflows/            Workflow exportável n8n
tests/                Testes automatizados com mocks
docs/                 Arquitetura e organização das capturas reais
data/                 Banco SQLite local (ignorado pelo Git)
PLANO_IMPLEMENTACAO.md fases e registro de execução
AGENTS.md             regras permanentes de trabalho
```

## Limitações conhecidas e evolução

- Não há autenticação de usuários finais nesta versão demonstrativa.
- O destino é demonstrado pelo registro do departamento no backend; não há sistema externo real de atendimento.
- O provedor precisa suportar Chat Completions e resposta estruturada por `response_format: json_schema` (modo estrito); a resposta também é validada localmente com Pydantic.
- A conectividade futura com IA/n8n depende das credenciais e da disponibilidade dos serviços externos; as capturas atuais documentam uma execução sintética real, sem dados pessoais.
- Próximas evoluções possíveis: fila assíncrona, histórico de múltiplas retentativas, autenticação de usuários, migrações Alembic e integrações autorizadas com ferramentas de suporte.

## Publicação

O repositório está preparado para Git local. Não versionar `.env`, banco local ou credenciais. Não publique o projeto nem faça push sem autorização explícita.
