# Feature 5 — Listagem de salas reservadas (usuario)
# Ana Sofia

Feature: Listagem de salas reservadas usuario
  Como um servico de listagem de reservas
  Quero recuperar e filtrar reservas por usuario e status
  Para que o sistema retorne o estado interno correto das reservas cadastradas

  Scenario: Recuperar todas as reservas de um usuario sem filtro de status
    Given o sistema possui reservas do CPF "11122233344" com status "pending" e "confirmed"
    When o servico de listagem e consultado para o CPF "11122233344" sem filtro de status
    Then o sistema retorna todas as reservas associadas ao CPF "11122233344"

  Scenario: Recuperar reservas de um usuario filtradas por status pendente
    Given o sistema possui uma reserva do CPF "11122233344" com status "pending" da sala "D005" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And o sistema possui uma reserva do CPF "11122233344" com status "confirmed" da sala "E101" das "2026-07-02T08:00:00" as "2026-07-02T10:00:00"
    When o servico de listagem e consultado para o CPF "11122233344" com filtro de status "pending"
    Then o sistema retorna somente reservas com status "pending" para o CPF "11122233344"

  Scenario: Recuperar reservas de um usuario filtradas por status confirmada
    Given o sistema possui uma reserva do CPF "11122233344" com status "pending" da sala "D005" das "2026-07-03T08:00:00" as "2026-07-03T10:00:00"
    And o sistema possui uma reserva do CPF "11122233344" com status "confirmed" da sala "E101" das "2026-07-04T08:00:00" as "2026-07-04T10:00:00"
    When o servico de listagem e consultado para o CPF "11122233344" com filtro de status "confirmed"
    Then o sistema retorna somente reservas com status "confirmed" para o CPF "11122233344"

  Scenario: Reservas retornadas ordenadas por data de inicio decrescente
    Given o sistema possui uma reserva do CPF "11122233344" com status "pending" da sala "D005" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And o sistema possui uma reserva do CPF "11122233344" com status "pending" da sala "E101" das "2026-07-10T08:00:00" as "2026-07-10T10:00:00"
    When o servico de listagem e consultado para o CPF "11122233344" sem filtro de status
    Then o sistema retorna as reservas ordenadas da mais recente para a mais antiga

  Scenario: Recuperar detalhes de uma reserva pertencente ao usuario
    Given o sistema possui uma reserva do CPF "11122233344" com status "pending" da sala "D005" das "2026-07-05T08:00:00" as "2026-07-05T10:00:00"
    When o servico de detalhe e consultado para o CPF "11122233344" e o id da reserva
    Then o sistema retorna os dados da reserva com sala "D005" e status "pending"

  Scenario: Tentativa de acesso a reserva pertencente a outro usuario
    Given o sistema possui uma reserva de outro usuario com CPF "99988877766" da sala "D005" das "2026-07-06T08:00:00" as "2026-07-06T10:00:00"
    When o servico de detalhe e consultado para o CPF "11122233344" e o id da reserva do outro usuario
    Then o sistema rejeita o acesso com erro "Acesso negado"

  Scenario: Consulta de listagem para usuario sem reservas cadastradas
    Given o sistema nao possui reservas para o CPF "11122233344"
    When o servico de listagem e consultado para o CPF "11122233344" sem filtro de status
    Then o sistema retorna uma colecao vazia de reservas

  Scenario: Consulta de listagem sem identificacao de usuario
    When o servico de listagem e consultado sem informar o CPF do usuario
    Then o sistema rejeita a requisicao por ausencia de parametro obrigatorio