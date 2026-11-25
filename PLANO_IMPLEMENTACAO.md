# Plano de implementação — AtendeAI

Este arquivo é o registro de execução do projeto. Atualize os estados, resultados, arquivos e pendências ao concluir cada fase, para permitir retomar o trabalho com clareza.

## Estado atual

- **Fase em andamento neste clone:** fases 5–7 concluídas com validação Playwright em desktop/mobile, revisão das capturas reais e correções de acessibilidade/responsividade. O fluxo integrado com `gemini-3.5-flash-lite` já foi validado. As capturas reais do frontend e do n8n foram concluídas; resta a revisão final da entrega.
- **Última atualização:** 2026-11-25.
- **Histórico da máquina anterior:** as fases e validações registradas abaixo descrevem a execução anterior e não substituem as verificações neste clone. A inspeção desta máquina encontrou o projeto versionado na branch `main`, sincronizada com `origin/main`; não havia alterações rastreadas pendentes.
- **Fase 1:** concluída com este plano e as regras de trabalho em `AGENTS.md`.
- **Ambiente local atual:** `uv 0.13.10`, CPython `3.11.18`, `.venv311` com dependências instaladas. O `.env` permanece ignorado pelo Git; somente `APP_PORT` foi ajustada localmente para `8001`, preservando o uso da porta `8000` pelo outro projeto.
- **Validação neste clone:** `25 passed, 1 warning` com Pytest no Python 3.11; `22 passed` em Playwright (desktop Chromium e viewport móvel); `docker compose config --quiet` passou. API e n8n estão saudáveis; `/health` retorna HTTP 200; o banco foi confirmado vazio após a validação visual.
- **n8n atual:** workflow importado e ativo, com credenciais funcionando: a sonda autenticada alcançou o callback e o teste sintético completou o encaminhamento. Volume persistente mantido. Nenhuma chamada adicional à IA foi feita durante a validação das fases 5–7.
- **Critério de transparência:** distinguir sempre entre implementado, testado automaticamente, testado manualmente, dependente de configuração/credenciais e pendente de execução externa.
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
- [x] **Fase 5 — Design system e estrutura do frontend.** Revisado em navegador Playwright em desktop e viewport móvel; navegação responsiva, temas e ausência de overflow horizontal validados. Capturas reais das telas sem dados registradas.
- [x] **Fase 6 — Funcionalidades do frontend.** Navegação, criação/validação/resultado/erro, Inbox, filtros/paginação/detalhes/retentativa, Analytics e Configurações percorridos em Chromium desktop e mobile. A suíte usa respostas isoladas e não grava dados nem chama IA/n8n.
- [x] **Fase 7 — Animações e acabamento.** Movimento reduzido, foco por teclado, estado acessível do menu móvel e acessibilidade WCAG verificados com axe-core nos principais estados/telas e nos dois temas; sem violações críticas ou sérias.
- [x] **Fase 8 — Docker e integração completa.** Dockerfile e Compose construídos; API e n8n saudáveis, comunicação interna confirmada e persistência do SQLite/workflow/credenciais verificada após reiniciar os containers neste clone.
- [ ] **Fase 9 — Testes e documentação.** README, arquitetura, Playwright e capturas reais do frontend/n8n atualizados; 25 testes Python e 22 cenários de navegador passaram. **Pendente:** revisão final da entrega.

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

### Configuração do ambiente neste clone — 2026-11-24

- **Python/uv:** instalado `uv 0.13.10` e Python `3.11.18`; criado `.venv311` e instaladas as dependências de `requirements.txt` usando `uv pip`. O `uv venv` não incluiu `pip` no ambiente por padrão; por isso, a instalação foi feita pelo próprio `uv`.
- **Porta:** a porta publicada da API foi alterada somente no `.env` local para `8001`; a porta `8000` ocupada pelo outro projeto não foi interrompida. O mapeamento é host `8001` → container `8000`; o callback n8n continua usando o DNS interno `http://api:8000`.
- **Docker:** `docker compose up --build -d` concluiu; API e n8n estão healthy. Foi criado o volume `atendeai-desafio-kodie-i_n8n_data`. Portas host `8001` e `5678` estão em uso pelo Compose.
- **Testes/verificações:** Pytest — `18 passed, 1 warning` de depreciação Starlette/httpx; Compose config válida; health HTTP 200 da API e n8n; API container alcançou `http://n8n:5678/healthz` com HTTP 200. Nenhuma chamada real ao modelo de IA foi executada.
- **n8n manual:** conta inicial, importação do workflow, credenciais Header Auth, expressão do callback e ativação foram concluídas pelo usuário e verificadas pelas sondas. Pendências: persistência após restart, conferência visual e eventual teste real da IA (chamada externa).
- **Arquivos de código:** nenhum arquivo rastreado foi alterado nesta configuração; `.env` e `.venv311` são locais/ignorados. Não houve commit nem push.

### Validação da integração n8n neste clone — 2026-11-24

- **Sonda de conectividade:** `docker compose exec -T api python -m scripts.check_n8n_webhook` confirmou `N8N_WEBHOOK=ACTIVE`, `WEBHOOK_AUTH=OK` e `INTERNAL_API_AUTH=OK`; o callback autenticado foi alcançado sem criar registro.
- **Teste positivo ponta a ponta:** a matriz sintética exercitou `support`, `financial`, `commercial` e `customer_service`. Os quatro webhooks retornaram HTTP 200; em todos, o callback persistiu o departamento correto, `Routing.status=completed` e `Attendance.status=routed`. Cada registro criado foi removido individualmente; a verificação final confirmou `MATRIX_RECORDS_REMAINING=0`.
- **Pendências identificadas naquele momento:** o teste ainda não exercitava classificação real pela IA nem persistência após restart; a persistência foi validada na seção seguinte. Capturas e conferências visuais do frontend/n8n continuam pendentes.

### Validação após reinício neste clone — 2026-11-24

- **Persistência SQLite:** o banco estava vazio antes do teste. Foi criado um único atendimento sintético, confirmado após `docker compose restart api n8n` e removido em seguida; as tabelas `attendances`, `classifications` e `routings` voltaram a zero registros. Nenhum volume foi removido.
- **Serviços e n8n:** após o reinício, `/health` da API e `/healthz` do n8n responderam HTTP 200; ambos ficaram `healthy` no Compose. A sonda `scripts.check_n8n_webhook` confirmou webhook ativo e autenticações do webhook/callback aceitas, indicando que workflow e credenciais continuaram disponíveis.
- **Frontend:** `/`, `assets/css/main.css` e `assets/js/app.js` responderam HTTP 200. Uma captura real do dashboard em desktop foi revisada e salva em `docs/screenshots/frontend/dashboard.png`; mostra o estado vazio e a API online. Isso não valida as demais telas, breakpoints mobile, interações nem o n8n visualmente.
- **IA real:** uma chamada sintética anterior a `scripts.check_ai_connection --timeout 120` excedeu o timeout; uma nova tentativa controlada retornou HTTP 503. O teste integrado por API permanece pendente da disponibilidade do provedor.
- **Validações:** `.venv311\Scripts\python.exe -m pytest -q` — 18 passaram, 1 aviso de depreciação Starlette/httpx; `docker compose config --quiet` passou.
- **Pendências:** revisar as demais telas e breakpoints mobile, validar o workflow visualmente no n8n e registrar as capturas restantes; repetir o fluxo integrado quando o provedor estiver estável.

### Nova sondagem do provedor de IA — 2026-11-24

- **Pré-condições:** API e n8n estavam saudáveis; as tabelas do banco estavam vazias.
- **Teste:** `docker compose exec -T -e AI_MAX_RETRIES=0 api python -m scripts.check_ai_connection --timeout 90` enviou uma única classificação sintética, sem retentativas.
- **Resultado:** o provedor respondeu HTTP 503. A sonda direta não cria atendimento nem chama o n8n; portanto, nenhum registro foi criado e o fluxo integrado não foi exercitado.
- **Ação naquele momento:** a tentativa foi interrompida após o HTTP 503. Uma nova sondagem direta passou conforme registrado abaixo; o teste integrado pelo endpoint permanece pendente.

### Reteste da IA após HTTP 503 — 2026-11-24

- **Resultado:** a tentativa 1 de 10 foi bem-sucedida; o provedor retornou classificação válida (`complaint/support/high`, sentimento negativo, confiança 0.95, sem revisão humana) para a mensagem sintética do script.
- **Comando:** `docker compose exec -T -e AI_MAX_RETRIES=0 api python -m scripts.check_ai_connection --timeout 90`. O `AI_MAX_RETRIES=0` foi aplicado somente ao processo desta chamada; nenhum arquivo, `.env` ou configuração persistente foi alterado. Não foi necessário restaurar configuração.
- **Escopo:** a sonda validou o serviço direto de IA; não criou atendimento no SQLite nem acionou n8n. Por solicitação, as tentativas pararam no primeiro sucesso; não foi feito o teste integrado pela API.

### Tentativas integradas IA→API→n8n — 2026-11-24

- **Teste:** foram feitas 10 submissões sequenciais ao endpoint HTTP real da API, com mensagem sintética sem dados pessoais e `source` exclusivo por tentativa. A política normal `AI_MAX_RETRIES=2` foi mantida; nenhuma configuração persistente foi alterada.
- **Resultados:** tentativas 1, 2 e 5 excederam o timeout da IA; tentativas 3, 4 e 6–10 terminaram em indisponibilidade HTTP 503 do provedor. Nenhuma chegou à etapa de encaminhamento no n8n.
- **Chamadas ao provedor:** como a API manteve dois retries para respostas HTTP transitórias, as sete submissões encerradas em 503 podem representar 21 chamadas ao provedor; os três timeouts não são repetidos. O script registrou os resultados finais por submissão, não cada chamada individual.
- **Limpeza:** os dez atendimentos sintéticos e seus dados relacionados foram removidos individualmente. A conferência final confirmou zero registros em `attendances`, `classifications` e `routings`.
- **Serviços:** API e n8n permaneceram `healthy`; `/health` respondeu HTTP 200. O teste não conclui uma falha do n8n, pois a classificação da IA falhou antes do despacho.

### Script simples para testar o provedor de IA — 2026-11-24

- **Implementação:** adaptado `scripts/check_ai_connection.py` para aceitar `--message`, `--timeout` e `--max-retries`. Por padrão usa texto sintético e zero retries, imprimindo JSON validado com provedor, modelo, duração, tamanho da entrada e classificação; erros informam tipo/status sem exibir chave ou mensagem enviada.
- **Documentação:** README atualizado com exemplos local/Docker e explicação de que retries adicionais são opt-in.
- **Testes:** três testes novos mockados cobrem sucesso, HTTP 503 sem vazamento de credenciais e argumentos CLI. Pytest — 21 passaram, 1 aviso de depreciação; `compileall`, `--help` e `docker compose config --quiet` passaram.
- **Limite da validação:** nenhuma chamada real ao provedor foi feita após essa alteração; os testes do script usam mock.

### Troca local para Gemini 3.5 Flash-Lite — 2026-11-24

- **Configuração:** `AI_MODEL` local e o padrão de `.env.example` agora usam `gemini-3.5-flash-lite`; o exemplo também usa a base OpenAI-compatible oficial do Gemini. Chave, timeout de 90 s e política normal `AI_MAX_RETRIES=2` foram preservados.
- **Container:** imagem da API reconstruída e somente o serviço API recriado; n8n e volumes não foram removidos. O container confirma o novo modelo e a versão atual do script. API e n8n saudáveis; healthchecks HTTP 200.
- **Teste real direto:** `docker compose exec -T api python -m scripts.check_ai_connection --timeout 90 --max-retries 0` — sucesso em 1,14 s, modelo `gemini-3.5-flash-lite`, classificação `complaint/support/high`, confiança 0.95 e sem revisão humana. Foi uma chamada externa; a sonda não cria atendimento nem chama n8n.
- **Testes automatizados:** Pytest — 21 passaram, 1 aviso de depreciação Starlette/httpx; `compileall`, `--help` do script e `docker compose config --quiet` passaram.
- **Pendência à época:** ainda não havia sido feito `POST /api/v1/attendances` real usando o novo modelo; a sonda cobria o serviço de IA diretamente e a suíte automatizada usava mocks.

### Validação integrada com Gemini 3.5 Flash-Lite — 2026-11-25

- **Teste:** duas submissões sintéticas, sequenciais e sem dados pessoais, ao endpoint HTTP real `POST /api/v1/attendances`.
- **Resultado:** ambas retornaram HTTP 502 com a mensagem sanitizada “O provedor de IA retornou uma resposta inválida.”; por isso, a classificação não chegou ao encaminhamento do n8n. O teste não distingue se a resposta era JSON malformado ou JSON que não atendia ao schema.
- **Limpeza:** os dois atendimentos e dados relacionados foram removidos individualmente. Verificação final: zero registros em `attendances`, `classifications` e `routings`.
- **Serviços:** API e n8n continuaram saudáveis e `/health` respondeu HTTP 200. O n8n não foi acionado por essas requisições.
- **Leitura:** a sonda direta do mesmo modelo passou, então configuração/chave/modelo conseguem se comunicar; as duas respostas inválidas na rota real indicam que ainda precisamos investigar a conformidade da resposta com o contrato Pydantic antes de considerar a integração concluída.

### Resolução e revalidação do contrato de IA — 2026-11-25

- **Correção:** `app/services/ai_service.py` agora envia JSON Schema estrito, com enumerações alinhadas aos enums Pydantic, `additionalProperties=false` e todos os campos obrigatórios. Temperatura passou a zero; a validação Pydantic permanece como segunda barreira.
- **Diagnóstico seguro:** falhas de envelope, recusa, truncamento, conteúdo vazio, parse JSON e schema recebem `failure_stage`. Logs registram etapa/modelo e nomes/tipos de campos inválidos, sem conteúdo da mensagem ou credenciais; o endpoint mantém mensagem genérica ao usuário.
- **Script:** `scripts/check_ai_connection.py` inclui a etapa da falha e status upstream quando houver, sem imprimir entrada ou chave.
- **Automatizado:** Pytest — 25 passaram, 1 aviso de depreciação Starlette/httpx; `compileall` e `docker compose config --quiet` passaram.
- **Ponta a ponta:** uma chamada real ao `POST /api/v1/attendances` retornou HTTP 201, modelo `gemini-3.5-flash-lite`, classificação `complaint/support/high`, confiança 0.95, atendimento `routed` e encaminhamento n8n `completed`. O detalhe confirmou persistência.
- **Limpeza/configuração:** registro sintético removido e confirmado ausente; tabelas de atendimentos, classificações e rotas ficaram vazias. `AI_MAX_RETRIES=0` foi temporário apenas para este teste e restaurado para 2; API e n8n terminaram `healthy`.

### Fases 5–7 — validação visual e funcional do frontend — 2026-11-25

- **Ferramentas:** adicionados Playwright e axe-core como dependências de desenvolvimento isoladas em `tests/e2e/`; testes em Chromium desktop (1440×1000) e em viewport móvel (390×844). Nenhum pacote de teste foi adicionado à imagem de produção.
- **Cobertura de navegador:** navegação e estados vazios; persistência dos temas; validação e envio do formulário com resposta simulada; tratamento de erro; busca/filtros/paginação da Inbox; detalhes/retentativa; Analytics/período; overflow; navegação por toque/teclado; foco visível; movimento reduzido; auditoria axe-core nas cinco áreas e nos temas claro/escuro.
- **Correções encontradas pelos testes:** contraste abaixo de WCAG em textos e badges; botão icon-only sem nome acessível; menu móvel ainda focável quando fechado; overflow horizontal na Inbox mobile; Analytics mostrava um gráfico vazio quando a série continha apenas zeros. Cores/tokens, nome acessível, `inert`/`aria-expanded`, layout e condição de estado vazio foram corrigidos.
- **Capturas reais:** `npm.cmd --prefix tests/e2e run capture:ui` criou `new-attendance.png`, `inbox.png`, `analytics.png`, `settings-dark.png`, `settings-light.png`, `mobile-dashboard.png` e `mobile-inbox.png` em `docs/screenshots/frontend/`. O script consulta a API real e recusa capturar se houver atendimentos no banco; a API retornou `total=0`. A captura anterior `dashboard.png` foi preservada.
- **Resultado:** Playwright — 22 testes passaram (11 por viewport); axe-core — nenhuma violação crítica/séria nas telas e temas avaliados. Revisão visual das capturas confirmou os principais layouts desktop/mobile, incluindo os estados vazios e formulário. Os testes de resultado/detalhes usam fixtures isoladas apenas como artefatos de inspeção e não são publicados como prova de execução real.
- **Demais verificações:** Pytest — 25 passaram, 1 aviso de depreciação Starlette/httpx; `compileall`, sintaxe dos testes Playwright, `docker compose config --quiet` passaram. `npm install` reportou zero vulnerabilidades. API e n8n permaneceram saudáveis; banco SQLite continuou vazio. A imagem da API foi reconstruída para servir os arquivos atualizados; volumes não foram removidos.
- **Pendências:** não foi feita chamada adicional ao provedor de IA nem criada classificação real para captura. Resultado/detalhes com dados reais e documentação visual do n8n ficam para a fase 9.

### Capturas reais de resultado e detalhes — 2026-11-25

- **Pré-verificação:** Git estava limpo; API e n8n estavam `healthy`, `/health` e `/healthz` responderam HTTP 200, a sonda autenticada confirmou webhook/callback ativos e o banco começou vazio.
- **Execução demonstrativa:** Playwright enviou pela interface uma mensagem sintética, sem dados pessoais. O `POST /api/v1/attendances` retornou HTTP 201; classificação `request/support/medium`, confiança 1.0, sem revisão humana; encaminhamento n8n `completed`, atendimento `routed` e execução n8n `13`. O endpoint de detalhes confirmou a mesma execução persistida.
- **Capturas revisadas:** `docs/screenshots/frontend/classification-result.png` mostra o resultado real; `docs/screenshots/frontend/attendance-details.png` mostra os detalhes retornados pela API. Ambas foram visualmente inspecionadas e não contêm credenciais ou dados pessoais.
- **Limpeza:** uma primeira submissão sintética foi removida exatamente após a revisão detectar problema de codificação no texto da captura. Após validar as capturas finais, o segundo registro também foi removido pelo ID exato; os totais de `attendances`, `classifications` e `routings` voltaram a zero. A execução n8n `13` permanece no histórico do n8n para as capturas visuais.
- **Pendência:** o n8n exige login na interface. Foi aberta uma janela local temporária do Playwright para autenticação manual; nenhuma senha foi solicitada ou registrada. Após login, capturar workflow, execução e configurações seguras dos nodes, remover o registro sintético e confirmar o banco vazio.

### Capturas reais do n8n — 2026-11-25

- **Login/diagnóstico:** a autenticação fornecida foi aceita em um contexto Chromium limpo. O workflow carregou como publicado e as chamadas normais da interface retornaram HTTP 200, sem erros JavaScript. Os relógios do host e do container estavam sincronizados; o token observado tinha expiração futura. Uma chamada manual isolada ao REST sem o header `browser-id` retornou 401 e não representava o fluxo normal do editor. Nenhuma senha ou token foi registrada no repositório.
- **Execução documentada:** workflow `AtendeAI — Roteamento de atendimentos`, ativo/publicado; execução real `13`, sucesso em 154 ms, ramo `support`, callback ao FastAPI HTTP 200 e retorno `completed`. A captura foi feita na UI real do n8n.
- **Capturas:** `docs/screenshots/workflow/atendeai-workflow.png`; `docs/screenshots/executions/execution-13-success.png`; configurações em `docs/screenshots/nodes/`; dados do callback e resposta em `docs/screenshots/results/`.
- **Segurança/revisão:** imagens revisadas; nenhuma chave ou valor de credencial aparece. Os detalhes do callback contêm somente campos sintéticos de roteamento e cabeçalhos de resposta não sensíveis. A sessão autenticada temporária foi armazenada fora do repositório e removida após as capturas.
- **Limpeza final:** o atendimento sintético exato já havia sido removido; `attendances`, `classifications` e `routings` permaneceram vazias. A API e o n8n permaneceram saudáveis.
- **Pendência geral:** revisão final da entrega da Fase 9.
