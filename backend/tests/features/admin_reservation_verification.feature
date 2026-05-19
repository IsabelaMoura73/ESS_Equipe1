# Feature: Verificacao de Reservas (servico - administrador)
# Cenarios orientados a servico: descrevem operacoes e efeitos no estado
# interno do sistema, sem referencia a elementos de interface.

Feature: Verificacao de Reservas servico
  Como administrador autenticado
  Quero confirmar ou negar reservas e consultar a listagem priorizada
  Para gerenciar a alocacao e o estado das salas

  Scenario: Listagem prioriza reservas de docentes
    Given existe a reserva "1" associada ao papel "discente" para a sala "Lab 1" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And existe a reserva "2" associada ao papel "docente" para a sala "Lab 2" das "2026-07-02T08:00:00" as "2026-07-02T10:00:00"
    When o servico retorna a listagem de reservas
    Then a reserva "2" aparece antes da reserva "1"
    And o status de ambas permanece "pending"

  Scenario: Confirmar uma reserva pendente
    Given existe a reserva "105" para a sala "Lab 1" com status "pending"
    When o administrador solicita a confirmacao da reserva "105"
    Then o status da reserva "105" passa a ser "confirmed"
    And o servico retorna a mensagem "Reserva confirmada com sucesso"

  Scenario: Negar uma reserva pendente sem justificativa
    Given existe a reserva "106" para a sala "Auditorio" com status "pending"
    When o administrador solicita a negacao da reserva "106" sem informar justificativa
    Then o status da reserva "106" passa a ser "denied"
    And o servico retorna a mensagem "Reserva negada com sucesso"

  Scenario: Reserva ja decidida e imutavel
    Given existe a reserva "107" para a sala "Grad 3" com status "confirmed"
    When o administrador solicita a confirmacao da reserva "107"
    Then o servico rejeita a operacao com a mensagem "Reserva ja decidida nao pode ser alterada"
    And o status da reserva "107" permanece "confirmed"

  Scenario: Servico expoe somente as acoes confirmar e negar
    Given existe a reserva "108" criada por "Professor Carlos" para a sala "Grad 4" com status "pending"
    When o administrador consulta o detalhe da reserva "108"
    Then o servico informa as acoes permitidas como "confirm,deny"
    And o servico nao expoe operacao para alterar os dados da reserva "108"
