# Capturas de execução

As capturas de frontend são feitas pelo Playwright no AtendeAI efetivamente executado. As telas vazias usam a API real e o script `tests/e2e/capture-ui.js` aborta quando há atendimentos no banco, para evitar capturar dados existentes. Resultado e detalhes foram capturados separadamente durante uma execução real de ponta a ponta com mensagem sintética, sem dados pessoais; não são fixtures nem mockups.

- `workflow/`: visão completa do workflow n8n ativo.
- `executions/`: execução real bem-sucedida.
- `nodes/`: configuração dos nodes, ocultando valores de credenciais.
- `results/`: payload/resultados da execução, sem dados pessoais ou segredos.
- `frontend/`: telas vazias e resultado/detalhes reais do AtendeAI.

## Frontend

- `frontend/dashboard.png`: dashboard com API conectada e banco vazio.
- `frontend/new-attendance.png`, `inbox.png`, `analytics.png`, `settings-dark.png` e `settings-light.png`: telas desktop, com banco vazio.
- `frontend/mobile-dashboard.png` e `frontend/mobile-inbox.png`: telas em viewport móvel, com banco vazio.
- `frontend/classification-result.png`: resultado real da classificação `request/support/medium`, encaminhamento concluído e confiança 100%; mensagem sintética e sem dados pessoais.
- `frontend/attendance-details.png`: detalhes do mesmo atendimento, confirmados no endpoint da API e com encaminhamento concluído.

## n8n

- `workflow/atendeai-workflow.png`: workflow publicado completo, com os quatro ramos de departamento e os caminhos de validação/erro.
- `executions/execution-13-success.png`: execução real `13` com o caminho `support` concluído, nodes executados marcados na UI.
- `nodes/webhook-settings.png`: método/path e URL de produção do webhook; credencial selecionada sem valor secreto.
- `nodes/validation-settings.png`: código de validação do payload.
- `nodes/department-router-settings.png`: regras de roteamento dos quatro departamentos.
- `nodes/fastapi-callback-settings.png`: configuração do callback HTTP ao FastAPI; a credencial aparece apenas pelo nome.
- `nodes/webhook-response-settings.png`: resposta estruturada ao backend.
- `results/fastapi-callback-200.png`: saída real do callback, HTTP 200 e encaminhamento `completed`.
- `results/webhook-response-result.png`: resposta final da mesma execução, incluindo departamento `support` e execução `13`.

As capturas foram feitas na interface n8n efetivamente autenticada. Os dados da execução são sintéticos e não pessoais. Não aparecem tokens, chaves nem valores de credenciais.
