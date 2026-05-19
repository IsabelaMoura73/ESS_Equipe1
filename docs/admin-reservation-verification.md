# Verificação de Reservas (Administrador)

Documentação da feature `features/admin-reservation-verification.feature`,
implementada no backend FastAPI do projeto Salla.

## 1. Visão geral

A feature permite que um administrador autenticado:

1. Visualize a listagem de todas as reservas cadastradas, com prioridade para
   reservas feitas por **docentes/professores**.
2. **Confirme** uma reserva pendente.
3. **Negue** uma reserva pendente (sem necessidade de justificativa).
4. Visualize os detalhes de uma reserva já decidida sem poder reverter a decisão.
5. Acesse uma reserva alheia em modo de leitura, com apenas as ações
   `Confirmar`/`Negar` habilitadas.

## 2. Arquivos criados / alterados

| Arquivo | Tipo | Descrição |
|---|---|---|
| `backend/routes/admin_reservation.py` | novo | Router com os endpoints de administração |
| `backend/schemas/admin_reservation.py` | novo | Schemas Pydantic de listagem, detalhe e resposta de ação |
| `backend/main.py` | alterado | Registro do `admin_reservation_router` |
| `backend/tests/features/admin_reservation_verification.feature` | novo | Cenários Gherkin para BDD |
| `backend/tests/test_admin_reservation_verification.py` | novo | Step definitions `pytest-bdd` |

Nenhum modelo (`models/reservation.py`) foi alterado: a feature consome o campo
`user_type` que já existia no modelo (`"student"`/`"teacher"` ou
`"discente"`/`"docente"`).

## 3. Endpoints

Todos os endpoints estão sob o prefixo `/api/admin/reservations`.

### 3.1 `GET /api/admin/reservations`

Lista todas as reservas. A ordenação é:

1. `user_type` pertencente ao conjunto `{teacher, docente, professor}` → vem antes.
2. Empate é resolvido por `start_time` ascendente.

Resposta `200 OK`: lista de `AdminReservationListItem` contendo `user_type` para
que o frontend possa exibir o badge de prioridade.

### 3.2 `GET /api/admin/reservations/{id}`

Retorna os detalhes da reserva acrescidos de três campos auxiliares:

- `can_confirm` (bool) — `true` apenas quando o status é `pending`.
- `can_deny` (bool) — idem.
- `read_only_fields` (lista) — campos que a UI deve renderizar como
  somente-leitura para o admin (`room`, `start_time`, `end_time`,
  `user_cpf`, `user_name`).

Esse contrato cobre os cenários 4 e 5 da feature: o frontend usa essas flags
para desabilitar os botões e travar o campo "Nome da sala".

Respostas:

- `200 OK` — `AdminReservationDetail`.
- `404 Not Found` — reserva inexistente.

### 3.3 `PATCH /api/admin/reservations/{id}/confirm`

Confirma uma reserva pendente.

- `200 OK` — `{ "message": "Reserva confirmada com sucesso", "reservation": {...} }`
- `400 Bad Request` — reserva não está em `pending` (`"Reserva já decidida..."`).
- `404 Not Found` — id inexistente.

### 3.4 `PATCH /api/admin/reservations/{id}/deny`

Nega uma reserva pendente. Não exige justificativa (a feature explicita isso no
cenário 3).

- `200 OK` — `{ "message": "Reserva negada com sucesso", "reservation": {...} }`
- `400 Bad Request` / `404 Not Found` — análogos ao confirm.

## 4. Regras de negócio implementadas

| ID | Regra | Onde |
|----|-------|------|
| RN-A1 | Reservas de docentes/professores aparecem antes das de discentes/alunos | `routes/admin_reservation.list_all_reservations` via `CASE` no `ORDER BY` |
| RN-A2 | Confirmar/Negar só são válidos para reservas `pending` | `routes/admin_reservation._decide` |
| RN-A3 | Reservas já decididas (`confirmed`/`denied`/`completed`) são somente-leitura | `can_confirm`/`can_deny` = `false` no detalhe + 400 nas rotas de ação |
| RN-A4 | Admin não pode editar dados de reserva alheia | Não há endpoint de edição; o detalhe expõe `read_only_fields` para a UI |
| RN-A5 | Negar dispensa justificativa | `PATCH /deny` não recebe body |
| RN-A6 | Mensagens em português conforme a feature | Strings literais em `_decide` |

## 5. Testes (BDD)

Os cenários da feature foram traduzidos para o arquivo
`backend/tests/features/admin_reservation_verification.feature`, mantendo o
mesmo padrão dos demais arquivos da pasta `backend/tests/features/`.

### 5.1 Estrutura

`test_admin_reservation_verification.py` segue o mesmo template de
`test_reservation.py` e `test_list_reservation.py`:

- **Banco em memória SQLite** com `StaticPool` — isolamento total entre testes.
- **Fixture `clean_database`** (autouse) — limpa tabelas e popula salas
  (`Lab 1`, `Lab 2`, `Auditorio`, `Grad 3`, `Grad 4`) antes de cada teste.
- **`override_get_db`** — substitui a dependência do FastAPI para usar o banco
  de teste.
- **`ROLE_MAP`** — traduz `"Aluno"`/`"Professor"` (linguagem da feature) para
  os valores armazenados (`"discente"`/`"docente"`).
- **`STATUS_MAP`** — converte strings em valores `ReservationStatus`.

### 5.2 Mapeamento cenário ↔ teste

| Cenário da feature | Função de teste gerada | Endpoints exercitados |
|---|---|---|
| Visualização com prioridade para professores | `test_visualizacao_da_listagem_com_prioridade_para_professores` | `GET /api/admin/reservations` |
| Confirmar reserva pendente | `test_confirmar_uma_reserva_pendente_com_sucesso` | `PATCH .../{id}/confirm` |
| Negar reserva pendente sem justificativa | `test_negar_uma_reserva_pendente_sem_justificativa` | `PATCH .../{id}/deny` |
| Tentar reverter reserva já decidida | `test_tentativa_de_reverter_uma_reserva_ja_decidida` | `GET .../{id}` + `PATCH .../confirm` |
| Editar dados de reserva alheia | `test_tentativa_de_editar_os_dados_de_uma_reserva_alheia` | `GET .../{id}` |

### 5.3 Como rodar

```bash
cd backend
# garanta DATABASE_URL definido (por exemplo, no .env)
pytest tests/test_admin_reservation_verification.py -v
```

Resultado esperado: **5 passed**.

## 6. Decisões de projeto

- **Ações via `PATCH` com endpoints dedicados** (`/confirm`, `/deny`) em vez de
  um único `PATCH` recebendo `status`. Isso evita que o admin tente forçar
  estados inválidos (como voltar para `pending`) e deixa o contrato explícito.
- **Flags `can_confirm`/`can_deny`/`read_only_fields` no detalhe**: o backend
  serve a fonte da verdade sobre o que está habilitado. O frontend apenas
  reflete o estado, sem duplicar a regra de negócio (cenários 4 e 5).
- **Sem alterações no modelo**: a feature reusa `user_type` já existente.
  O conjunto `TEACHER_TYPES = {"teacher", "docente", "professor"}` aceita os
  sinônimos possíveis dependendo de qual outra feature alimente o campo.
