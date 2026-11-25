# AtendeAI

**Triagem inteligente de atendimentos, com classificação estruturada e encaminhamento demonstrável.** O AtendeAI combina interface web, API FastAPI, **Google Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)**, SQLite e automação n8n. O backend acessa o modelo pela API Gemini compatível com OpenAI Chat Completions.

[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue.svg)](LICENSE)

O projeto foi desenvolvido como solução demonstrativa para o desafio técnico KODIE de integração entre inteligência artificial, API e automação. A classificação é feita no backend; o n8n registra o departamento de destino no próprio AtendeAI. Não há integração com uma plataforma externa de atendimento.

## Navegação

- [Problema e proposta](#problema-e-proposta)
- [IA e classificação com Gemini](#ia-e-classificação-com-gemini)
- [Funcionalidades](#funcionalidades)
- [Contexto do desafio](#contexto-do-desafio)
- [Documentação](#documentação)
- [Demonstração visual](#demonstração-visual)
- [Arquitetura e fluxo](#arquitetura-e-fluxo)
- [Decisões de projeto](#decisões-de-projeto)
- [Tecnologias](#tecnologias)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Workflow n8n](#workflow-n8n)
- [Como executar](#como-executar)
- [Configuração e segurança](#configuração-e-segurança)
- [Testes e limitações](#testes-e-limitações)

## Problema e proposta

Pequenas equipes podem receber mensagens de clientes com dúvidas, reclamações, solicitações e elogios. A triagem manual exige leitura, identificação de prioridade e encaminhamento ao setor adequado; esse trabalho pode consumir tempo e atrasar o atendimento.

O AtendeAI demonstra como organizar essa etapa: a pessoa registra uma mensagem, a API solicita uma classificação estruturada à IA, valida e persiste o resultado e, quando não é necessária revisão humana, aciona o n8n para registrar o departamento de destino. A interface permite acompanhar indicadores e consultar atendimentos.

A classificação inclui categoria, departamento, prioridade, sentimento, resumo, confiança estimada, justificativa e indicação de revisão humana. A confiança é uma estimativa do modelo, não uma garantia estatística. Casos marcados para revisão — ou abaixo do limite configurado — não são encaminhados automaticamente.

## IA e classificação com Gemini

O **Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) é o motor de classificação do AtendeAI**. Ele transforma cada mensagem livre em dados de triagem estruturados, interpretando conteúdo e intenção — não apenas palavras-chave — e produz categoria, departamento, prioridade, sentimento, resumo, confiança estimada, justificativa e necessidade de revisão humana.

A API envia a mensagem junto ao prompt especializado [`prompts/message_classification.md`](prompts/message_classification.md) e solicita uma resposta em JSON conforme um JSON Schema estrito. Em seguida, o backend valida o resultado com Pydantic, aplica o limite configurado de confiança e decide se o atendimento pode seguir para o n8n ou deve aguardar revisão humana.

O `.env.example` configura esse modelo pelo endpoint Gemini compatível com OpenAI Chat Completions. `AI_MODEL` e `AI_BASE_URL` continuam configuráveis; a classificação permanece no backend e o navegador nunca chama o modelo diretamente.

## Funcionalidades

- Criar atendimentos com mensagem e dados de cliente opcionais.
- Classificar mensagens em categorias, departamentos, prioridades e sentimentos definidos.
- Consultar resumo, justificativa, confiança estimada e necessidade de revisão humana.
- Persistir atendimentos, classificações e estado de encaminhamento em SQLite.
- Buscar, filtrar, paginar e consultar detalhes na Inbox.
- Visualizar indicadores, distribuições e volume ao longo do tempo.
- Demonstrar o roteamento para quatro departamentos pelo workflow n8n.
- Retentar encaminhamentos elegíveis sem apagar a classificação já concluída.
- Usar a interface em temas claro e escuro, com layout responsivo.

## Contexto do desafio

O AtendeAI foi desenvolvido no contexto do desafio técnico KODIE, com foco em demonstrar a integração entre inteligência artificial, API Python/FastAPI, validação de respostas estruturadas, persistência e automação com n8n. A solução reúne esses componentes em um fluxo demonstrável de ponta a ponta sem afirmar integrações externas que não existem.

## Documentação

- [Arquitetura](docs/architecture.md)
- [API e contratos](docs/API.md)
- [Workflow n8n e configuração](docs/WORKFLOW_N8N.md)
- [Desenvolvimento, testes e sondas](docs/DEVELOPMENT.md)
- [Índice das capturas reais](docs/screenshots/README.md)

## Demonstração visual

As imagens abaixo são capturas reais do AtendeAI. As telas de estado vazio usam a API em execução; resultado e detalhes foram registrados com mensagem sintética, sem dados pessoais.

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/frontend/dashboard.png" alt="Dashboard do AtendeAI com indicadores zerados e gráficos no estado vazio" width="100%"><p><strong>Visão geral.</strong> Indicadores e gráficos baseados nos dados persistidos.</p></td>
    <td width="50%"><img src="docs/screenshots/frontend/new-attendance.png" alt="Formulário para criar atendimento e enviar uma mensagem para classificação" width="100%"><p><strong>Novo atendimento.</strong> Entrada de mensagem e dados opcionais do cliente.</p></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/frontend/classification-result.png" alt="Resultado real de classificação sintética, com categoria, departamento, prioridade, sentimento e encaminhamento concluído" width="100%"><p><strong>Resultado da IA.</strong> Classificação sintética real, encaminhada pelo n8n.</p></td>
    <td width="50%"><img src="docs/screenshots/frontend/inbox.png" alt="Inbox do AtendeAI no estado vazio, com busca e filtros" width="100%"><p><strong>Inbox.</strong> Busca, filtros e paginação dos atendimentos.</p></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/frontend/attendance-details.png" alt="Detalhes de atendimento demonstrativo, incluindo mensagem original, classificação e encaminhamento" width="100%"><p><strong>Detalhes.</strong> Informações do atendimento confirmadas pela API.</p></td>
    <td width="50%"><img src="docs/screenshots/frontend/analytics.png" alt="Tela de Analytics do AtendeAI com distribuições e série temporal" width="100%"><p><strong>Analytics.</strong> Distribuições e evolução dos registros.</p></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/frontend/settings-dark.png" alt="Tela de configurações do AtendeAI no tema escuro" width="100%"><p><strong>Tema escuro.</strong> Preferências e estado configurado dos serviços.</p></td>
    <td width="50%"><img src="docs/screenshots/frontend/settings-light.png" alt="Tela de configurações do AtendeAI no tema claro" width="100%"><p><strong>Tema claro.</strong> Alternância de aparência da interface.</p></td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/screenshots/frontend/mobile-dashboard.png" alt="Dashboard do AtendeAI em viewport móvel" width="100%"><p><strong>Dashboard móvel.</strong> Layout adaptado a telas pequenas.</p></td>
    <td width="50%"><img src="docs/screenshots/frontend/mobile-inbox.png" alt="Inbox do AtendeAI em viewport móvel" width="100%"><p><strong>Inbox móvel.</strong> Navegação e consulta responsivas.</p></td>
  </tr>
</table>

## Arquitetura e fluxo

```mermaid
flowchart TD
    U[Pessoa usuária] --> FE[Frontend HTML CSS JavaScript]
    FE -->|HTTP mesma origem| API[API FastAPI]
    API -->|Carrega| P[Prompt de classificação]
    API -->|Chat Completions com JSON Schema estrito| AI[Google Gemini 3.5 Flash-Lite]
    AI -->|Resposta JSON| API
    API -->|Persiste atendimento e classificação| DB[(SQLite)]
    API -->|Se revisão humana não for necessária| N8N[Webhook n8n]
    N8N --> V[Validação e escolha do departamento]
    V -->|Callback com token interno| API
    API -->|Atualiza encaminhamento| DB
    N8N -->|Resposta síncrona| API
    API -->|Resultado consolidado| FE
    FE --> U
```

1. A interface envia a mensagem à API; o navegador não chama diretamente IA, banco ou n8n.
2. A API valida e persiste o atendimento e envia a mensagem, tratada como dado não confiável, ao serviço de IA junto ao prompt.
3. A resposta estruturada é validada por JSON Schema estrito e por Pydantic. O backend aplica o limite de confiança e a regra de revisão humana.
4. Se houver revisão, o encaminhamento automático fica bloqueado. Caso contrário, a API chama o webhook n8n server-to-server.
5. O n8n valida o payload, escolhe um de quatro departamentos e chama o callback autenticado da API para registrar o resultado.
6. A API atualiza o estado persistido e devolve o resultado ao frontend.

Se o n8n não estiver configurado ou falhar, a classificação permanece armazenada e o estado do encaminhamento pode ser consultado. O n8n demonstra o registro do destino no AtendeAI; não cria chamados em um serviço externo.

## Decisões de projeto

- **Backend como fonte da verdade:** valida entradas e saídas, aplica regras de revisão, persiste os dados e expõe uma API única para o frontend.
- **Resposta de IA estruturada:** JSON Schema estrito reduz variações no formato; Pydantic faz a validação local antes de persistir.
- **Gemini e automação com responsabilidades distintas:** o Gemini classifica a mensagem no backend; o n8n decide o ramo e registra o encaminhamento sem incorporar as regras centrais de classificação.
- **Falha do encaminhamento não apaga a classificação:** os estados de classificação e de roteamento são mantidos separadamente para permitir consulta e retentativa elegível.
- **Stack leve para demonstração:** frontend sem framework pesado, SQLite e Compose simplificam a execução local do conjunto.

## Tecnologias

| Categoria | Tecnologias | Uso no projeto |
|---|---|---|
| Frontend | HTML, CSS, JavaScript ES6+ | Interface estática servida pela própria API. |
| Recursos visuais | Chart.js, Lucide, Google Fonts (DM Sans e Manrope) | Gráficos, ícones e fontes carregados no frontend por CDN. |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy, HTTPX | API, validação, persistência e chamadas HTTP assíncronas. |
| Inteligência artificial | **Google Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`)** via API Gemini compatível com OpenAI Chat Completions | Classifica cada mensagem e gera os campos estruturados que o backend valida com JSON Schema e Pydantic. |
| Automação | n8n | Validação do payload, roteamento por departamento e callback à API. |
| Armazenamento | SQLite | Atendimentos, classificações e encaminhamentos locais. |
| Infraestrutura | Docker, Docker Compose | Execução da API e do n8n com persistência local. |
| Testes | Pytest, Playwright, axe-core | Testes de backend e de navegador, incluindo verificações de acessibilidade. |

O modelo de referência é o Gemini 3.5 Flash-Lite; `AI_MODEL` e `AI_BASE_URL` permitem configurar outro endpoint compatível que aceite `response_format: json_schema` estrito. `AI_PROVIDER` não seleciona adaptadores independentes por fornecedor.

## Estrutura do projeto

```text
app/                 API, schemas, serviços, modelos e persistência
frontend/            Interface HTML, CSS e JavaScript
prompts/             Prompt de classificação e casos de avaliação
workflows/           Exportação JSON do workflow n8n
tests/               Testes Python e testes de navegador
scripts/             Sondas para IA e webhook n8n
docs/                Arquitetura, API, desenvolvimento e workflow
  screenshots/       Capturas reais do frontend e do n8n
data/                Banco SQLite local (não versionado)
Dockerfile           Imagem da API
docker-compose.yml   API e n8n com persistência
requirements.txt     Dependências Python
```

## Workflow n8n

O n8n recebe a classificação pronta da API; **a IA não é executada dentro do workflow**. O fluxo valida o payload, direciona para `support`, `financial`, `commercial` ou `customer_service`, registra o destino no callback protegido da API e responde ao webhook.

![Workflow n8n completo do AtendeAI, com validação, quatro departamentos e callback](docs/screenshots/workflow/atendeai-workflow.png)

*Visão geral do workflow publicado na instância usada na demonstração. O arquivo exportado no repositório está inativo por padrão e exige configuração de credenciais antes da publicação.*

![Execução real bem-sucedida do workflow n8n pelo ramo de suporte](docs/screenshots/executions/execution-13-success.png)

*Execução demonstrativa com mensagem sintética e callback concluído.*

Capturas reais das configurações dos nodes de webhook, validação, decisão, roteamento, destinos, tratamento de erros, callback e resposta estão em [`docs/screenshots/`](docs/screenshots/). A documentação detalhada está em [`docs/WORKFLOW_N8N.md`](docs/WORKFLOW_N8N.md).

O [índice visual](docs/screenshots/README.md) relaciona as capturas reais e suas finalidades.

## Como executar

### Docker Compose — caminho recomendado

Pré-requisitos: Docker Desktop ou Docker Engine com Docker Compose.

No PowerShell, na raiz do projeto:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edite `.env` e configure `AI_API_KEY`, `N8N_API_TOKEN` e `INTERNAL_API_TOKEN`. Use tokens longos e diferentes. Se trocar de provedor, ajuste `AI_BASE_URL` e `AI_MODEL`. Em seguida:

```powershell
docker compose up --build
```

Acesse:

- AtendeAI: `http://localhost:8000`
- n8n: `http://localhost:5678`
- Swagger/OpenAPI da API: `http://localhost:8000/docs`

A stack contém a API (que também serve o frontend) e o n8n. O banco SQLite é persistido em `./data`; os dados do n8n ficam no volume `n8n_data`. O workflow precisa ser importado, receber as credenciais e ser publicado no n8n. Veja [Workflow n8n](#workflow-n8n) e o [guia completo](docs/WORKFLOW_N8N.md).

### Execução local da API

Requer Python 3.11 ou superior. No PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Configure a IA em `.env` e inicie a API, que serve também o frontend:

```powershell
uvicorn app.main:app --reload
```

Sem um n8n acessível e `N8N_WEBHOOK_URL` configurado, a API pode classificar e persistir atendimentos, mas o encaminhamento permanecerá pendente. Para executar todos os componentes juntos, prefira Compose.

## Configuração e segurança

- `.env.example` contém nomes e valores de exemplo; as credenciais ficam vazias. Copie-o para `.env` e não versione o arquivo local.
- `.env` e o banco local são ignorados pelo Git. Tokens também devem ser configurados como credenciais no n8n; nunca os inclua no workflow exportado, README ou screenshots.
- O callback interno exige `INTERNAL_API_TOKEN`; o webhook n8n exige `N8N_API_TOKEN`.
- O provedor de IA recebe o texto submetido para classificação. Revise as condições de privacidade do provedor e use dados sintéticos ou autorizados.
- Esta versão não tem autenticação de usuário final e não deve ser exposta publicamente sem controles de acesso e hardening adicionais.

## Testes e limitações

Os testes de backend usam SQLite temporário e mocks; a suíte Playwright usa respostas da API simuladas. Portanto, testes automatizados não substituem uma validação com credenciais reais e os serviços externos disponíveis.

- Backend: `python -m pytest -q`
- Playwright, sondas de integração e detalhes de execução: [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

### Estado atual

- **Implementado:** interface, API, classificação estruturada, persistência SQLite, Inbox, analytics, temas, roteamento demonstrativo para quatro departamentos e callback autenticado do n8n.
- **Dependente de configuração externa:** classificação real requer credenciais e um provedor compatível; o encaminhamento n8n requer importar o workflow, configurar credenciais e publicá-lo.
- **Não implementado nesta versão:** login/gestão de usuários e integração com CRM ou plataforma externa de atendimento. SQLite e Compose estão preparados para demonstração local, não para uma implantação multiusuário de produção.
- **Evoluções possíveis, não disponíveis hoje:** autenticação de usuários, processamento assíncrono, histórico detalhado de cada tentativa e integrações externas autorizadas.
- **Documentação visual:** inclui capturas reais das telas do frontend, da execução do workflow n8n e das configurações dos nodes e caminhos de erro.

---

Desenvolvido no contexto do desafio técnico KODIE, com foco na integração entre IA, API, persistência e automação.
