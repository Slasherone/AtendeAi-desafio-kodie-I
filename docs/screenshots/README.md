# Capturas de execução

As capturas de frontend são feitas pelo Playwright no AtendeAI efetivamente executado, com dados reais da API. O script recusa a captura quando há atendimentos no banco; não use mockups ou telas simuladas como evidência.

- `workflow/`: visão completa do workflow n8n ativo.
- `executions/`: execução real bem-sucedida e, se disponível, tratamento de falha.
- `nodes/`: configuração dos nodes, ocultando valores de credenciais.
- `results/`: payload/resultados da execução, sem dados pessoais ou segredos.
- `frontend/`: Dashboard, Novo atendimento, Inbox, Analytics, temas e viewport mobile.

Capturas reais disponíveis:

- `frontend/dashboard.png`: dashboard com API conectada e banco vazio, capturado anteriormente.
- `frontend/new-attendance.png`, `inbox.png`, `analytics.png`, `settings-dark.png` e `settings-light.png`: desktop, banco vazio.
- `frontend/mobile-dashboard.png` e `frontend/mobile-inbox.png`: viewport móvel, banco vazio.

Resultado/detalhes com classificação real não foram capturados nesta etapa, para evitar uma chamada desnecessária ao provedor externo de IA. Os testes Playwright de resultado e detalhes usam fixtures isoladas e não são apresentados como evidência de execução real. Capturas do workflow e execuções n8n permanecem fora do escopo das fases 5–7.
