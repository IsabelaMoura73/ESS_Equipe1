# Verificação de Reservas (Administrador) — Service Scenarios

Documentação da feature `features/admin-reservation-verification.feature`,
implementada no backend FastAPI do projeto Salla.

Os cenários desta feature são **service/controller scenarios**: descrevem
operações expostas pelo serviço e seus efeitos no estado interno do sistema,
**sem** referência a telas, botões, campos ou navegação da interface gráfica.
Eles complementam — não substituem — eventuais cenários de UI que a equipe de
frontend venha a definir.

## 1. Visão geral

A feature define cinco operações do serviço de administração de reservas:

1. **Consultar listagem priorizada** — reservas de docentes/professores
   precedem as de discentes/alunos.
2. **Confirmar** uma reserva pendente.
3. **Negar** uma reserva pendente (sem justificativa).
4. **Imutabilidade** — reservas já decididas (`confirmed`, `denied`,
   `completed`) não podem ter o status alterado.
5. **Superfície restrita** — o serviço expõe ao administrador apenas as ações
   `confirm` e `deny`; não há operação para alterar os dados da reserva.

## 2. Arquivos criados / alterados

| Arquivo | Tipo | Descrição |
|---|---|---|
| `backend/routes/admin_reservation.py` | novo | Router com os endpoints de administração |
| `backend/schemas/admin_reservation.py` | novo | Schemas Pydantic (listagem, detalhe, ação) |
| `backend/main.py` | alterado | Registro do `admin_reservation_router` |
| `backend/tests/features/admin_reservation_verification.feature` | novo | Cenários Gherkin (service-level) |
| `backend/tests/test_admin_reservation_verification.py` | novo | Step definitions `pytest-bdd` |
| `features/admin-reservation-verification.feature` | reescrito | Versão canônica em estilo service |

Nenhum modelo foi alterado: a feature consome o campo `user_type` que já
existia em `models/reservation.py`.

## 3. Endpoints

Todos os endpoints estão sob `/api/admin/reservations`.

### 3.1 `GET /api/admin/reservations`

Lista todas as reservas. Ordenação:

1. `user_type` ∈ `{teacher, docente, professor}` → vem antes.
2. Empate por `start_time` ascendente.

`200 OK` → lista de `AdminReservationListItem` (inclui `user_type`).

### 3.2 `GET /api/admin/reservations/{id}`

Retorna o detalhe acrescido de:

- `allowed_actions: list[str]` — ações que o serviço aceita para a reserva no
  estado atual. Vale `["confirm", "deny"]` quando `status == pending`, lista
  vazia caso contrário.

Esse campo é o ponto de contato com o requisito de imutabilidade e de
superfície restrita: o serviço declara explicitamente o que pode ser feito.

Respostas:

- `200 OK` — `AdminReservationDetail`.
- `404 Not Found` — reserva inexistente.

### 3.3 `PATCH /api/admin/reservations/{id}/confirm`

- `200 OK` — `{ "message": "Reserva confirmada com sucesso", "reservation": {...} }`
- `400 Bad Request` — status diferente de `pending` (`"Reserva já decidida não pode ser alterada"`).
- `404 Not Found` — id inexistente.

### 3.4 `PATCH /api/admin/reservations/{id}/deny`

Não recebe body (negação não exige justificativa).

- `200 OK` — `{ "message": "Reserva negada com sucesso", "reservation": {...} }`
- `400` / `404` análogos ao confirm.

### 3.5 Operações ausentes propositalmente

`PUT`, `PATCH` (raiz) e `DELETE` em `/api/admin/reservations/{id}` **não
existem**. Isso é parte do contrato: o admin não altera dados da reserva.
Qualquer chamada a esses verbos retorna `404` ou `405`, o que é verificado pelo
cenário 5.

## 4. Regras de negócio

| ID | Regra | Onde |
|----|-------|------|
| RN-A1 | Reservas de docentes precedem as de discentes na listagem | `list_all_reservations`, `CASE` no `ORDER BY` |
| RN-A2 | `confirm` e `deny` só atuam em reservas `pending` | `_decide` em `routes/admin_reservation.py` |
| RN-A3 | Reserva decidida é imutável (status não regride nem muda) | `_decide` retorna 400 + `allowed_actions=[]` no detalhe |
| RN-A4 | Admin não pode editar dados da reserva | Ausência intencional de endpoint de edição |
| RN-A5 | Negar não exige justificativa | `PATCH /deny` não aceita body |
| RN-A6 | Mensagens em PT-BR como na feature | Literais em `_decide` |

## 5. Testes (BDD)

Os cenários foram traduzidos para
`backend/tests/features/admin_reservation_verification.feature`, mantendo o
mesmo padrão dos demais arquivos da pasta `backend/tests/features/`.

### 5.1 Estrutura

`test_admin_reservation_verification.py` segue o template de
`test_reservation.py` e `test_list_reservation.py`:

- **Banco SQLite em memória** com `StaticPool` — isolamento por teste.
- **Fixture `clean_database`** (autouse) — limpa tabelas e popula as salas
  `Lab 1`, `Lab 2`, `Auditorio`, `Grad 3`, `Grad 4`.
- **`override_get_db`** — substitui a dependência do FastAPI pelo banco de teste.
- **`STATUS_MAP`** — converte strings em valores `ReservationStatus`.

### 5.2 Mapeamento cenário ↔ teste

| Cenário (service) | Função de teste | Endpoints exercitados |
|---|---|---|
| Listagem prioriza reservas de docentes | `test_listagem_prioriza_reservas_de_docentes` | `GET /api/admin/reservations` |
| Confirmar uma reserva pendente | `test_confirmar_uma_reserva_pendente` | `PATCH .../{id}/confirm` |
| Negar uma reserva pendente sem justificativa | `test_negar_uma_reserva_pendente_sem_justificativa` | `PATCH .../{id}/deny` |
| Reserva já decidida é imutável | `test_reserva_ja_decidida_e_imutavel` | `PATCH .../{id}/confirm` (esperando 400) |
| Serviço expõe somente as ações confirmar e negar | `test_servico_expoe_somente_as_acoes_confirmar_e_negar` | `GET .../{id}` + `PUT/PATCH/DELETE` (esperando 404/405) |

### 5.3 Como rodar

```bash
cd backend
# garanta DATABASE_URL definido (por exemplo, no .env)
pytest tests/test_admin_reservation_verification.py -v
```

Resultado esperado: **5 passed**.

## 6. Por que cenários de serviço (e não de UI)

Conforme orientação do material da disciplina, cenários de serviço:

- Não mencionam elementos da interface (botões, campos, páginas), abstrações
  de UI ou navegação.
- Focam em **ações** expostas pelo sistema e nos **efeitos** sobre o estado
  interno (status no banco, ordem da listagem retornada, ações declaradas
  como permitidas).
- Tornam explícitas requisições e respostas da API.

Essa feature foi reescrita para se enquadrar no critério. A versão inicial,
com passos como "clica no botão Confirmar" ou "o campo Nome da sala permanece
no modo somente leitura", foi substituída por:

- "o administrador solicita a confirmação da reserva 105"
- "o serviço informa as ações permitidas como confirm,deny"
- "o serviço não expõe operação para alterar os dados da reserva 108"

## 7. Decisões de projeto

- **Endpoints dedicados `/confirm` e `/deny`** em vez de um `PATCH` genérico
  com `status` no body — impede transições inválidas e deixa o contrato
  explícito.
- **`allowed_actions` no detalhe** — o serviço é a fonte da verdade sobre o
  que pode ser feito. A UI apenas reflete esse estado (e existe um cenário de
  serviço que cobre a presença/ausência dessas ações).
- **Sem endpoint de edição para o admin** — testado por ausência: o cenário 5
  verifica que `PUT`/`PATCH`/`DELETE` retornam 404 ou 405.
- **Reuso de `user_type`** — `TEACHER_TYPES = {"teacher", "docente",
  "professor"}` aceita sinônimos vindos das demais features.
