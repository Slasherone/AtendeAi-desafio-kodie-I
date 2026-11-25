# API AtendeAI

Este documento descreve os contratos implementados pela API FastAPI. A interface interativa do FastAPI também fica disponível em `/docs` quando a aplicação está em execução.

## Base e autenticação

Na configuração padrão, a API é servida na mesma origem que o frontend, em `http://localhost:8000`. Os endpoints de consulta e criação não exigem autenticação de usuário nesta versão demonstrativa. O callback interno usado pelo n8n exige `Authorization: Bearer <INTERNAL_API_TOKEN>`.

## Endpoints

| Método | Caminho | Finalidade |
|---|---|---|
| `GET` | `/health` | Verifica se a aplicação responde. |
| `GET` | `/api/v1/services/health` | Informa se há chave/modelo de IA e URL de webhook n8n configurados. Não verifica tokens nem conectividade externa. |
| `POST` | `/api/v1/attendances` | Cria um atendimento, solicita a classificação à IA e tenta iniciar o encaminhamento. |
| `GET` | `/api/v1/attendances` | Lista atendimentos, com busca, filtros e paginação. |
| `GET` | `/api/v1/attendances/{attendance_id}` | Consulta os detalhes de um atendimento. |
| `GET` | `/api/v1/classifications` | Lista classificações com paginação. |
| `POST` | `/api/v1/attendances/{attendance_id}/dispatch` | Retenta um encaminhamento elegível. |
| `GET` | `/api/v1/analytics/overview` | Retorna indicadores agregados. |
| `GET` | `/api/v1/analytics/distribution` | Retorna distribuições por categoria, departamento, prioridade e sentimento. |
| `GET` | `/api/v1/analytics/timeline?days=14` | Retorna volume diário no período solicitado. |
| `POST` | `/api/v1/internal/attendances/{attendance_id}/route` | Registra o resultado do workflow n8n; endpoint interno autenticado. |

## Criar atendimento

`POST /api/v1/attendances`

```json
{
  "customer_name": "Cliente de demonstração",
  "customer_email": "cliente@example.com",
  "source": "web",
  "message": "Não consigo acessar minha conta."
}
```

`customer_name` e `customer_email` são opcionais. `source` é opcional e assume `web` por padrão. A mensagem é obrigatória, não pode conter apenas espaços e aceita até 10.000 caracteres. O e-mail, quando informado, é validado.

Resposta de sucesso (`201 Created`), com valores ilustrativos:

```json
{
  "id": "uuid-do-atendimento",
  "status": "routed",
  "message": "Classificação concluída; encaminhamento registrado.",
  "classification": {
    "id": "uuid-da-classificacao",
    "category": "complaint",
    "department": "support",
    "priority": "high",
    "sentiment": "negative",
    "summary": "Cliente relata dificuldade para acessar a conta.",
    "confidence": 0.94,
    "requires_human_review": false,
    "reason": "A mensagem descreve um problema de acesso.",
    "review_reason": null,
    "model_name": "modelo-configurado",
    "prompt_version": "1.0"
  },
  "routing": {
    "id": "uuid-do-encaminhamento",
    "department": "support",
    "status": "completed",
    "execution_id": "id-da-execucao-n8n",
    "error_message": null,
    "attempts": 1,
    "created_at": "2026-11-25T12:00:00Z",
    "updated_at": "2026-11-25T12:00:01Z",
    "completed_at": "2026-11-25T12:00:01Z"
  },
  "created_at": "2026-11-25T12:00:00Z"
}
```

Os IDs e horários acima são exemplos, não dados de uma execução atual. `classification` e `routing` podem estar ausentes ou nulos em estados intermediários ou de falha. Se a revisão humana for necessária, o despacho automático fica bloqueado. Se o webhook n8n não estiver configurado, a classificação é mantida e o encaminhamento fica `pending`.

### Campos da classificação

| Campo | Valores ou significado |
|---|---|
| `category` | `question`, `complaint`, `request`, `compliment` ou `other` |
| `department` | `support`, `financial`, `commercial` ou `customer_service` |
| `priority` | `low`, `medium`, `high` ou `critical` |
| `sentiment` | `positive`, `neutral` ou `negative` |
| `summary` | Resumo em português, de até 500 caracteres |
| `confidence` | Estimativa do modelo entre `0` e `1`; não é garantia estatística |
| `requires_human_review` | Indica se a automação deve aguardar revisão |
| `reason` | Justificativa da classificação |

O backend exige revisão quando o modelo a sinaliza ou quando a confiança fica abaixo de `AI_CONFIDENCE_THRESHOLD` (padrão `0.70`).

## Listar e consultar atendimentos

`GET /api/v1/attendances`

Parâmetros disponíveis:

| Parâmetro | Padrão / valores aceitos |
|---|---|
| `page` | `1` ou maior |
| `page_size` | `20`; de `1` a `100` |
| `category` | Filtro por categoria |
| `department` | Filtro por departamento |
| `priority` | Filtro por prioridade |
| `sentiment` | Filtro por sentimento |
| `status` | Filtro pelo estado do atendimento |
| `requires_human_review` | `true` ou `false` |
| `search` | Busca por ID, cliente, mensagem original ou resumo; até 200 caracteres |
| `sort` | `desc` (padrão) ou `asc`, por data de criação |

A resposta inclui `items`, `total`, `page` e `page_size`. Cada item contém os dados resumidos do atendimento, sua classificação e seu encaminhamento quando disponíveis.

`GET /api/v1/attendances/{attendance_id}` retorna os detalhes, incluindo a mensagem original e o e-mail quando fornecidos. O endpoint responde `404` se o ID não existir.

`GET /api/v1/classifications?page=1&page_size=50` retorna uma lista de classificações. `page_size` aceita de `1` a `100`.

## Retentar encaminhamento

`POST /api/v1/attendances/{attendance_id}/dispatch`

Não requer body. Um atendimento sem classificação ou encaminhamento elegível, em revisão humana, já concluído ou em execução pode responder `409 Conflict`. Atendimento inexistente responde `404`. A API impede retentar casos que estejam aguardando revisão humana.

## Analytics

- `GET /api/v1/analytics/overview`: totais de atendimentos, classificados, encaminhamentos pendentes, concluídos, revisões humanas e falhas.
- `GET /api/v1/analytics/distribution`: contagens por categoria, departamento, prioridade e sentimento.
- `GET /api/v1/analytics/timeline?days=14`: série diária, de `1` a `365` dias. O padrão é `14`.

As métricas são calculadas a partir dos registros persistidos no SQLite. O período de `days` aplica-se à timeline; os endpoints de distribuição não recebem filtro de período.

## Callback interno do n8n

`POST /api/v1/internal/attendances/{attendance_id}/route`

Cabeçalho obrigatório:

```http
Authorization: Bearer <INTERNAL_API_TOKEN>
```

Body:

```json
{
  "department": "support",
  "status": "completed",
  "execution_id": "id-da-execucao-n8n",
  "error_message": null
}
```

`department` deve corresponder ao departamento persistido na classificação. `status` aceita `completed` ou `failed`; `execution_id` e `error_message` são opcionais. O backend recusa um departamento divergente, bloqueia encaminhamentos de casos em revisão humana e trata callbacks repetidos após conclusão sem criar um novo registro de encaminhamento.

O token ausente ou incorreto é rejeitado. O callback não deve ser chamado pelo navegador; é uma comunicação entre n8n e API.

## Respostas de erro mais comuns

| Código | Situação |
|---|---|
| `401` | Token interno ausente ou inválido. |
| `404` | Atendimento não encontrado. |
| `409` | Estado incompatível com retentativa, departamento divergente ou revisão humana pendente. |
| `422` | Body ou parâmetros inválidos. |
| `502` | Falha ou resposta inválida do provedor de IA. |
| `503` | IA não configurada ou integração interna sem configuração. |
