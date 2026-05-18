# Feature 5 — Listagem de salas reservadas (usuario)
# Aluna: Ana Sofia
# Persona BDD: Ana Lima

Feature: Listagem de salas reservadas usuario
  Como uma usuario autenticada do sistema Salla
  Quero visualizar a lista das minhas reservas de salas
  Para acompanhar o status de cada reserva e acessar seus detalhes

  Scenario: Listar todas as reservas sem filtro
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And Ana possui reservas com status "pending" e "confirmed"
    When Ana acessa a listagem de suas reservas
    Then a listagem retorna todas as reservas de Ana independente do status

  Scenario: Filtrar reservas por status pendente
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And Ana possui uma reserva com status "pending" da sala "D005" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And Ana possui uma reserva com status "confirmed" da sala "E101" das "2026-07-02T08:00:00" as "2026-07-02T10:00:00"
    When Ana filtra suas reservas por status "pending"
    Then a listagem retorna apenas reservas com status "pending"

  Scenario: Filtrar reservas por status confirmada
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And Ana possui uma reserva com status "pending" da sala "D005" das "2026-07-03T08:00:00" as "2026-07-03T10:00:00"
    And Ana possui uma reserva com status "confirmed" da sala "E101" das "2026-07-04T08:00:00" as "2026-07-04T10:00:00"
    When Ana filtra suas reservas por status "confirmed"
    Then a listagem retorna apenas reservas com status "confirmed"

  Scenario: Listagem ordenada da mais recente para a mais antiga
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And Ana possui uma reserva com status "pending" da sala "D005" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And Ana possui uma reserva com status "pending" da sala "E101" das "2026-07-10T08:00:00" as "2026-07-10T10:00:00"
    When Ana acessa a listagem de suas reservas
    Then a listagem esta ordenada da mais recente para a mais antiga

  Scenario: Visualizar detalhes de uma reserva especifica
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And Ana possui uma reserva com status "pending" da sala "D005" das "2026-07-05T08:00:00" as "2026-07-05T10:00:00"
    When Ana acessa os detalhes da sua reserva
    Then os detalhes exibem sala "D005" e status "pending"

  Scenario: Tentar acessar reserva de outro usuario
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    And existe uma reserva de outro usuario com CPF "99988877766" da sala "D005" das "2026-07-06T08:00:00" as "2026-07-06T10:00:00"
    When Ana tenta acessar os detalhes da reserva do outro usuario
    Then Ana recebe o erro "Acesso negado"

  Scenario: Listar reservas quando nao ha nenhuma cadastrada
    Given Ana Lima esta autenticada no sistema com CPF "11122233344"
    When Ana acessa a listagem de suas reservas
    Then a listagem retorna uma lista vazia

  Scenario: Tentar listar reservas sem informar o CPF
    When uma usuario nao autenticada tenta listar reservas sem informar o CPF
    Then o sistema retorna erro de validacao com codigo 422