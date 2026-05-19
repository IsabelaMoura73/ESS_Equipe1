# Feature: Verificacao de Reservas (Administrador)
# Persona BDD: Admin Salla

Feature: Verificacao de Reservas
  Como um administrador do sistema
  Quero visualizar, confirmar ou negar reservas de salas
  Para gerenciar a alocacao e o estado das salas adequadamente

  Scenario: Visualizacao da listagem com prioridade para professores
    Given o administrador autenticado acessa a pagina de Visualizacao de Reservas
    And o sistema possui a reserva "1" associada ao papel "Aluno" para a sala "Lab 1" das "2026-07-01T08:00:00" as "2026-07-01T10:00:00"
    And o sistema possui a reserva "2" associada ao papel "Professor" para a sala "Lab 2" das "2026-07-02T08:00:00" as "2026-07-02T10:00:00"
    When o sistema carrega a listagem de reservas cadastradas
    Then a reserva do professor e exibida antes da reserva do aluno na lista
    And o status de ambas permanece "pending"

  Scenario: Confirmar uma reserva pendente com sucesso
    Given o administrador autenticado acessa a pagina de Visualizacao de Reservas
    And existe a reserva "105" para a sala "Lab 1" com status "pending"
    When o administrador clica no botao Confirmar para a reserva "105"
    Then o sistema atualiza o status da reserva "105" para "confirmed" no banco de dados
    And o sistema retorna a mensagem de sucesso "Reserva confirmada com sucesso"

  Scenario: Negar uma reserva pendente sem justificativa
    Given o administrador autenticado acessa a pagina de Visualizacao de Reservas
    And existe a reserva "106" para a sala "Auditorio" com status "pending"
    When o administrador clica no botao Negar para a reserva "106"
    Then o sistema atualiza o status da reserva "106" para "denied" no banco de dados
    And o sistema retorna a mensagem de sucesso "Reserva negada com sucesso"

  Scenario: Tentativa de reverter uma reserva ja decidida
    Given o administrador autenticado acessa a pagina de Visualizacao de Reservas
    And existe a reserva "107" para a sala "Grad 3" com status "confirmed"
    When o administrador visualiza os detalhes da reserva "107"
    Then o sistema exibe os botoes Confirmar e Negar com o estado desabilitado
    And o sistema nao permite alterar o status da reserva "107"

  Scenario: Tentativa de editar os dados de uma reserva alheia
    Given existe a reserva "108" criada por "Professor Carlos" para a sala "Grad 4" com status "pending"
    When o administrador acessa os detalhes da reserva "108"
    Then o campo nome da sala consta como somente leitura
    And o administrador possui apenas as acoes Confirmar e Negar habilitadas
