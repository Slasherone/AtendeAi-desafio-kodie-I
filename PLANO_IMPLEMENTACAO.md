# Plano de implementação — AtendeAI

Este arquivo é o registro de execução do projeto. Atualize os estados, resultados, arquivos e pendências ao concluir cada fase, para permitir retomar o trabalho com clareza.

## Estado atual

- **Fase em andamento:** resiliência da classificação implementada para 503 e outros erros temporários; aguardar recuperação do provedor para reteste real. Depois, retomar a validação de persistência da Fase 8 e as conferências visuais pendentes.
- **Última atualização:** 2026-11-24.
- **Inspeção inicial:** concluída. A pasta continha somente `instrucoes_desafio.md`; não havia código, dependências, testes, `AGENTS.md` nem repositório Git. As verificações `git status`, `git branch` e `git log` confirmaram a ausência de metadados Git. O Git local foi inicializado durante a execução; nenhum commit ou push foi feito.
- **Fase 1:** concluída com este plano e as regras de trabalho em `AGENTS.md`.
- **Implementado nesta execução:** backend/API e modelos, serviço de IA e prompt, retries limitados para indisponibilidade temporária de IA, workflow n8n exportável, frontend, Docker/Compose, testes, documentação e configuração OpenCode MCP sem segredos.
- **Validação automatizada:** `18 passed, 1 warning` em Pytest no Python 3.11; `compileall`, verificação de sintaxe dos módulos JavaScript e `docker compose config --quiet` passaram.
- **Python do projeto:** Python 3.11.18 instalado pelo `uv` em runtime gerenciado fora do PATH global; `.venv311` criada localmente e ignorada pelo Git. A instalação Python 3.10 existente foi preservada.
- **IA/Gemini:** configuração ativa usa `openai_compatible` com modelo `gemini-3.8-flash` e chave presente (valor não exibido). A classificação real já havia funcionado anteriormente; na tentativa mais recente, o provedor respondeu HTTP 503 / `UNAVAILABLE`, com a mensagem de alta demanda temporária do modelo.
- **n8n/Docker:** Compose usa a imagem estável fixada `n8nio/n8n:2.48.7`. API e n8n estão em execução e saudáveis; `N8N_WEBHOOK_URL` usa `http://n8n:5678/webhook/atendeai/route`. Sonda e registro positivo ponta a ponta confirmaram URL, autenticação do webhook e callback interno, e persistência do resultado `routed/completed` antes da limpeza do registro sintético.
- **MCP OpenCode↔n8n:** `opencode.json` criado com endpoint local e referência `{env:N8N_MCP_TOKEN}`. Ainda requer habilitar Instance-level MCP, gerar token, permitir o workflow AtendeAI, definir variável de ambiente e reiniciar OpenCode.
- **GitHub:** `origin` aponta para `https://github.com/Slasherone/AtendeAi-desafio-kodie-I.git`; branch local `main`; o remoto consultado não apresentou refs. Não há commits locais nem publicação.
- **Fase em retomada:** requisição chegou à API, mas o Gemini respondeu 503 por alta demanda. Foram adicionados retries limitados e mensagem final mais clara. A validação após a mudança usa mocks; reteste real aguarda recuperação do provedor. Configurar MCP continua dependente do token local do usuário.
- **Critério de transparência:** distinguir sempre entre implementado, testado automaticamente, testado manualmente, dependente de configuração/credenciais e pendente de execução externa.

## Princípios e decisões de arquitetura

1. FastAPI é a fonte da verdade para validação, regras de negócio, persistência e dados consumidos pelo frontend.
2. Frontend estático (HTML, CSS e JavaScript ES6+) servido pela própria API; sem framework pesado e sem acesso direto ao provedor de IA, SQLite ou n8n.
3. Persistência SQLite com SQLAlchemy 2.x. Modelos de atendimento, classificação e encaminhamento mantêm os estados de classificação e roteamento distinguíveis.
4. Integração de IA configurável por ambiente e encapsulada em serviço; validar toda resposta com Pydantic. A suíte principal usa mocks, sem chamadas pagas/reais.
5. Revisão humana impede encaminhamento automático. Falha do n8n não invalida a classificação; novas tentativas devem ser autenticadas e idempotentes sempre que possível.
6. O n8n demonstra o roteamento registrando o departamento no backend; nenhuma integração externa de atendimento será inventada.
7. Segredos somente por ambiente/credenciais gerenciadas. Não versionar `.env`, credenciais nem valores reais.
8. Docker Compose deve permitir a API acessar o n8n pelo nome de serviço, persistindo SQLite e dados do n8n.

## Contratos funcionais previstos

### Classificação

`category`: `question | complaint | request | compliment | other`  
`department`: `support | financial | commercial | customer_service`  
`priority`: `low | medium | high | critical`  
`sentiment`: `positive | neutral | negative`  
Também obrigatórios: `summary`, `confidence` (0–1), `requires_human_review` e `reason`.

Confiança abaixo do limite configurável (padrão 0.70), ambiguidade ou insuficiência de contexto exigem revisão humana. Prioridade não deve ser inferida apenas do sentimento.

### API mínima

- `GET /health`
- `POST /api/v1/attendances`
- `GET /api/v1/attendances` (paginação, busca, filtros e ordenação)
- `GET /api/v1/attendances/{id}`
- `GET /api/v1/classifications`
- `POST /api/v1/internal/attendances/{id}/route` (token interno)
- `POST /api/v1/attendances/{id}/dispatch` (retentativa segura)
- `GET /api/v1/analytics/overview`
- `GET /api/v1/analytics/distribution`
- `GET /api/v1/analytics/timeline`

Os campos e códigos HTTP serão definidos em schemas coerentes; mensagens de erro não expõem stack traces ou credenciais.

### Fluxo n8n

FastAPI persiste atendimento → classifica via serviço de IA → valida/persiste classificação → se não exigir revisão, chama o webhook n8n server-to-server → n8n valida payload e roteia os quatro departamentos → n8n registra resultado no endpoint interno autenticado → devolve resultado estruturado à API → API responde ao frontend. Falhas deixam classificação disponível e encaminhamento pendente/falho para retentativa.

## Fases, entregáveis e critérios de conclusão

- [x] **Fase 1 — Inspeção e planejamento.** Verificar arquivos e estado Git, registrar arquitetura, contratos, dependências e etapas. Critério: plano consultável e regras de trabalho estabelecidas.
- [x] **Fase 2 — Estrutura e backend.** Configuração, FastAPI, banco/modelos, schemas, serviços, health e rotas de atendimento implementados. Testes da API passam com banco temporário e dependências mockadas.
- [x] **Fase 3 — Serviço de IA.** Prompt independente, cliente OpenAI-compatible configurável, validação JSON, confiança/revisão humana e testes mockados implementados. Casos de avaliação manual do prompt incluídos.
- [x] **Fase 4 — Automação n8n.** URL e credencial Header Auth corrigidas. Sonda de conectividade confirma autenticações e callback; execução positiva com registro sintético confirma resposta 200, encaminhamento `completed` e atendimento persistido como `routed`. O registro foi removido ao final do teste.
- [ ] **Fase 5 — Design system e estrutura do frontend.** Tokens CSS, temas, layout, sidebar, navegação, componentes e responsividade implementados. **Pendente:** conferência visual manual em desktop e mobile.
- [ ] **Fase 6 — Funcionalidades do frontend.** Dashboard, criação, resultado, Inbox, detalhes, Analytics e Configurações integrados à API implementados. Servimento dos arquivos estáticos foi verificado por teste; **pendente:** percorrer o fluxo em navegador.
- [ ] **Fase 7 — Animações e acabamento.** Feedback, loading/erro/vazio, modal/toasts, acessibilidade e `prefers-reduced-motion` implementados. **Pendente:** validação manual de usabilidade e acessibilidade visual.
- [ ] **Fase 8 — Docker e integração completa.** Dockerfile e Compose construídos; API e n8n iniciaram saudáveis e a comunicação interna foi confirmada. **Pendente:** testar persistência após reiniciar os containers.
- [ ] **Fase 9 — Testes e documentação.** Suíte, README, arquitetura e diretórios de capturas criados; 14 testes passam em Python 3.11. **Pendente:** capturas reais e revisão visual manual.

## Estrutura de arquivos planejada

```text
AGENTS.md
PLANO_IMPLEMENTACAO.md
app/
  api/routes/  core/  database/  models/  schemas/  services/
frontend/
  index.html  assets/css/  assets/js/  assets/images/
prompts/message_classification.md
workflows/atendeai-workflow.json
tests/
scripts/check_ai_connection.py
docs/architecture.md  docs/screenshots/{workflow,executions,nodes,results,frontend}/
data/  (dados locais ignorados pelo Git)
.env.example  .gitignore  Dockerfile  docker-compose.yml
requirements.txt  README.md  LICENSE
```

Manter a estrutura simples e sem camadas vazias; ajustá-la se o repositório evoluir de forma que justifique outra organização.

## Registro de execução por fase

### Fase 1 — Inspeção e planejamento (concluída)

- **Resultado:** diretório verificado; só havia o documento de requisitos e não havia repositório Git. Plano e regras de trabalho registrados.
- **Arquivos:** `PLANO_IMPLEMENTACAO.md`, `AGENTS.md`.
- **Testes:** não aplicável.
- **Pendências:** nenhuma para esta fase.
- **Próxima etapa:** Fase 2 — estrutura e backend.

### Fases 2–3 — Estrutura/backend e serviço de IA (implementadas e testadas)

- **Resultado:** API FastAPI, schemas Pydantic, persistência SQLAlchemy/SQLite, atendimento/classificação/encaminhamento, filtros/paginação, analytics, autenticação do callback interno, retentativa com claim atômico, cliente OpenAI-compatible, revisão humana e prompt independente.
- **Arquivos principais:** `app/`, `prompts/message_classification.md`, `prompts/classification_test_cases.json`, `tests/test_api.py`, `tests/test_classification.py`.
- **Testes:** `.venv311\Scripts\python.exe -m pytest -q` — 18 passaram no Python 3.11 (1 aviso Starlette/httpx); `python -m compileall -q app tests scripts` passou.
- **Pendências:** validar fluxo de atendimento completo no navegador após configurar o workflow n8n.
- **Próxima etapa:** configuração manual do workflow e testes integrados.

### Incidente de disponibilidade do provedor de IA — 2026-11-24

- **Sintoma:** o envio feito pelo frontend recebeu HTTP 502; a API registrou a tentativa como `classification_failed`, sem classificação. O frontend apresentou a mensagem genérica de erro do provedor.
- **Diagnóstico:** a sonda segura e duas chamadas sintéticas subsequentes receberam HTTP 503. O corpo do provedor indicou `UNAVAILABLE` porque o modelo estava com alta demanda temporária. A configuração efetiva mostra provedor `openai_compatible`, modelo `gemini-3.8-flash` e chave configurada; a falha não aponta para endpoint inválido, chave ausente ou defeito do frontend.
- **Estado:** a classificação por IA já deveria estar disponível nesta fase e foi validada com sucesso anteriormente; não é uma funcionalidade futura. O erro atual depende da disponibilidade do provedor externo. Não alteramos configuração nem removemos o atendimento que falhou.
- **Próxima ação:** a imagem da API já foi reconstruída; health HTTP 200 e ambiente efetivo `AI_MAX_RETRIES=2`, `AI_TIMEOUT=90`. Após o provedor sair de `UNAVAILABLE`, executar `docker compose exec -T api python -m scripts.check_ai_connection --timeout 120`; quando retornar `AI_CONNECTION=OK`, repetir uma mensagem sintética pela interface. O atendimento que falhou continua armazenado como `classification_failed` e poderá aparecer na Inbox.

### Resiliência da integração de IA — implementada

- **Mudança:** `AI_MAX_RETRIES` (padrão 2, configurável entre 0 e 3) repete respostas HTTP transitórias `429`, `500`, `502`, `503` e `504`; backoff exponencial de 1/2 s, respeita `Retry-After` numérico limitado a 5 s, e `AI_TIMEOUT` limita o tempo total da classificação. Erros de autenticação e timeouts não são repetidos.
- **Experiência de erro:** se o provedor permanecer indisponível após as tentativas, a API retorna uma mensagem orientando o usuário a tentar novamente, sem expor detalhes ou credenciais do provedor.
- **Validação automatizada:** testes com transporte HTTP mockado cobrem recuperação após 503, limite de tentativas, `Retry-After` limitado e ausência de retry em 401; suíte completa — 18 passaram, 1 aviso de depreciação. `compileall` e `docker compose config --quiet` passaram.
- **Aplicação:** imagem da API reconstruída; container healthy, `/health` HTTP 200 e `AI_MAX_RETRIES=2` confirmado no ambiente ativo. Nenhuma chamada real adicional foi feita ao Gemini durante esta mudança.
- **Pendência externa:** confirmar uma classificação real após o provedor sair de `UNAVAILABLE`.

### Fase 4 — Workflow n8n (concluída e validada ponta a ponta)

- **Resultado:** usuário importou `workflows/atendeai-workflow.json`; arquivo contém webhook, validação, quatro rotas, registro no FastAPI e resposta estruturada. Credenciais no export são placeholders e precisam de vínculo na UI.
- **Arquivos principais:** `workflows/atendeai-workflow.json`, `docs/architecture.md`, `README.md`, `tests/test_routing.py`.
- **Testes:** `docker compose exec -T api python -m scripts.check_n8n_webhook` — `N8N_WEBHOOK=ACTIVE; WEBHOOK_AUTH=OK; INTERNAL_API_AUTH=OK; callback reached the API`; o 404 para UUID inexistente é a resposta esperada da sonda. Teste positivo via webhook publicado — HTTP 200, encaminhamento `completed`, atendimento `routed`. `TEST_RECORD_CLEANUP=OK` confirmou remoção do registro sintético. Suíte completa — 14 passaram, um aviso de depreciação do Starlette/httpx; `docker compose config --quiet` passou. Estado dos containers: API e n8n saudáveis.
- **Causa raiz confirmada na execução real do n8n (execução 10):** o payload recebido pelo webhook tinha `body` com os campos esperados (`attendance_id`, `department`, `idempotency_key` etc.); validação e roteamento foram corretos. O node `Registrar encaminhamento no FastAPI` tinha URL salva como `=={{ 'http://api:8000/...` na versão publicada `549f2a2e-c1fa-4d66-8212-1a83c48eaa8e`. O n8n resolveu a URL para `=http://api:8000/...` e registrou `Invalid URL: ... URL must start with "http" or "https"`. Portanto, não era o input do atendimento nem o contrato da API; era um `=` excedente inserido no modo Expression.
- **Correção no repositório:** `workflows/atendeai-workflow.json` já contém a expressão exportada correta com um `=` inicial. O teste foi fortalecido para comparar a expressão completa e impedir regressão. O README agora instrui ativar **fx / Expression** e colar `{{ ... }}` sem `=`, verificando que o JSON exportado seja `={{ ... }}` (um único `=`).
- **Causa confirmada pelas capturas da credencial:** no formulário Header Auth, o campo **Name** continha `AtendeAI Internal API Auth`, mas esse campo é enviado como nome do header HTTP; os espaços inválidos causavam `ERR_INVALID_HTTP_TOKEN`. O **Value** estava sem o prefixo `Bearer ` exigido pelo backend. A tela diferencia o título da credencial desses dois campos. Usuário corrigiu os campos para o contrato esperado; os valores não foram registrados.
- **Validação positiva:** foi criado um atendimento sintético com UUID aleatório e classificação `support`; o workflow publicado chamou o callback, recebeu 200, e o banco refletiu `Routing.status=completed` e `Attendance.status=routed`. O script de teste removeu o atendimento, classificação e routing sintéticos, e confirmou que o ID não restou no banco. Nenhum atendimento anterior foi alterado.
- **Próximas etapas:** validar persistência do SQLite e do workflow/credenciais após reinício dos containers (Fase 8); fazer conferência visual do frontend em desktop/mobile e guardar capturas reais (Fases 5–7/9). O usuário optou por manter o token atual para o exercício local; nenhum valor secreto foi salvo neste plano.

### Fases 5–7 — Frontend (implementado; conferência no navegador pendente)

- **Resultado:** SPA em HTML/CSS/JavaScript puro, Dashboard, Novo atendimento, Inbox, detalhes, Analytics, Configurações, dark/light, estados vazios e responsividade declarada em CSS.
- **Arquivos principais:** `frontend/index.html`, `frontend/assets/css/`, `frontend/assets/js/`.
- **Testes:** `GET /`, `/health`, `/assets/css/main.css` e `/assets/js/app.js` responderam HTTP 200 no Compose ativo; sintaxe dos módulos JavaScript também foi verificada com Node. Isso valida entrega dos arquivos, não sua renderização visual. Não foi feita validação visual/manual em navegador.
- **Pendências:** percorrer fluxos, temas e breakpoints em desktop/mobile e registrar capturas reais.

### Fases 8–9 — Docker, testes e documentação (parcialmente validadas)

- **Resultado:** Dockerfile Python 3.11, Compose API+n8n, persistência, healthchecks, `.env.example`, `.gitignore`, README, arquitetura e instruções de capturas criados. A imagem n8n foi fixada na versão estável `2.48.7` após a tag genérica `:2` não existir.
- **Testes executados:** `.venv311\Scripts\python.exe -m pytest -q` — **14 passed, 1 warning**; `python -m compileall -q app tests scripts` passou; `node --input-type=module --check` passou para os sete módulos JavaScript; `docker compose config --quiet` passou; `docker build` passou; `docker compose up --build -d` iniciou API e n8n saudáveis. `/health` API e `/healthz` n8n responderam HTTP 200; API container acessou `http://n8n:5678/healthz` com HTTP 200. UI do n8n e frontend responderam HTTP 200.
- **Teste real de IA:** `python -m scripts.check_ai_connection` retornou `AI_CONNECTION=OK` para Gemini (`gemini-3.8-flash`), classificação `complaint/support/high`, confiança 0.95 e sem revisão humana no texto sintético de teste. A listagem autenticada de modelos retornou HTTP 200 e confirma o modelo configurado (IDs do Google aparecem com prefixo `models/`). Uma chamada do container expirou em 30 s; timeout foi elevado a 90 s; uma chamada posterior no container teve sucesso e outra retornou 503 transitório. A checagem local continuou passando. A chave não foi exibida.
- **Aviso de teste:** Starlette informa depreciação futura do uso de HTTPX no `TestClient`; não afeta o resultado atual.
- **Ambiente:** runtime Python 3.11.18 gerenciado pelo `uv`, `.venv311` local. Python 3.10 global permanece inalterado. `.env` continua ignorado pelo Git; valores secretos não foram exibidos.
- **Pendências externas/manuais:** ativar/corrigir o workflow e associar as credenciais na UI; repetir a sonda, testar encaminhamento real e persistência após restart; validar telas e gerar screenshots reais. A análise Gemini passou isoladamente no host e no container; o POST integrado ainda depende de disponibilidade momentânea do provedor e do webhook ativo.
- **Próximo passo:** na UI do n8n em `http://localhost:5678`, ativar o workflow e confirmar método/path/credenciais. Então executar `docker compose exec -T api python -m scripts.check_n8n_webhook` e repetir o teste de atendimento. A stack Compose está em execução. Para publicação GitHub, ainda é necessário criar commit e receber autorização explícita de push.
