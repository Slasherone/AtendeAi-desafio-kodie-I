# Capturas reais do AtendeAI

Este diretório contém capturas da interface do AtendeAI e da interface real do n8n. Não são mockups. As telas vazias do frontend foram registradas com a API em execução; `tests/e2e/capture-ui.js` verifica que o banco não contém atendimentos e cancela a captura se encontrar registros. Resultado e detalhes foram registrados em uma execução de ponta a ponta com mensagem sintética, sem dados pessoais.

Use as capturas com as legendas abaixo. Para o resumo visual no README, consulte [`../../README.md`](../../README.md); para a explicação completa da automação, consulte [`../WORKFLOW_N8N.md`](../WORKFLOW_N8N.md).

## Frontend

| Arquivo | O que demonstra |
|---|---|
| `frontend/dashboard.png` | Visão geral, serviços configurados e estado vazio do banco. |
| `frontend/new-attendance.png` | Formulário de criação de atendimento. |
| `frontend/classification-result.png` | Resultado real de uma classificação sintética: `request/support/medium`, encaminhamento concluído. |
| `frontend/inbox.png` | Inbox no estado vazio. |
| `frontend/attendance-details.png` | Detalhes do mesmo atendimento sintético, confirmados pela API. |
| `frontend/analytics.png` | Analytics no estado vazio. |
| `frontend/settings-dark.png`, `frontend/settings-light.png` | Configurações nos temas escuro e claro. |
| `frontend/mobile-dashboard.png`, `frontend/mobile-inbox.png` | Dashboard e Inbox em viewport móvel. |

## Workflow n8n

| Arquivo | O que demonstra |
|---|---|
| `workflow/atendeai-workflow.png` | Workflow publicado completo, com rotas por departamento e caminhos de erro. |
| `executions/execution-13-success.png` | Execução real bem-sucedida pelo ramo `support`. |
| `nodes/webhook-settings.png` | Método, caminho e autenticação do webhook; sem valor secreto. |
| `nodes/validation-settings.png` | Código de validação do payload. |
| `nodes/payload-validity-settings.png` | Condição do node IF que separa payload válido de inválido. |
| `nodes/department-router-settings.png` | Regras do Switch para os quatro departamentos. |
| `nodes/destination-support-settings.png` | Campos preparados pelo ramo `support`. |
| `nodes/destination-financial-settings.png` | Campos preparados pelo ramo `financial`. |
| `nodes/destination-commercial-settings.png` | Campos preparados pelo ramo `commercial`. |
| `nodes/destination-customer-service-settings.png` | Campos preparados pelo ramo `customer_service`. |
| `nodes/invalid-payload-settings.png` | Status, código HTTP e mensagem para payload inválido. |
| `nodes/unknown-department-settings.png` | Resposta para departamento sem ramo de destino. |
| `nodes/callback-error-settings.png` | Resposta de falha do callback ao FastAPI. |
| `nodes/fastapi-callback-settings.png` | Configuração do callback HTTP ao FastAPI; sem valor de credencial. |
| `nodes/webhook-response-settings.png` | Resposta estruturada ao backend. |
| `results/fastapi-callback-200.png` | Retorno real HTTP 200 do callback e encaminhamento `completed`. |
| `results/webhook-response-result.png` | Resposta final da execução, com departamento e ID de execução sintéticos. |

Não há node de IA no workflow: a classificação é executada pelo backend antes da chamada ao n8n. As capturas das configurações foram feitas na interface real do n8n, com pausas para carregamento entre as interações; não são imagens simuladas.

As capturas foram revisadas e não exibem tokens, chaves ou valores de credenciais. Os dados de execução visíveis são sintéticos. Não adicione dados pessoais ou informações de clientes a novas imagens.
