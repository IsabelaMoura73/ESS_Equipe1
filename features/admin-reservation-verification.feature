Feature: Verificação de Reservas (serviço)
  Como administrador autenticado
  Quero confirmar ou negar reservas de salas e consultar a listagem priorizada
  Para gerenciar a alocação e o estado das salas adequadamente

  # Persona BDD: Erick Teste (administrador)
  # Cenários service-level: descrevem operações do serviço e efeitos no estado
  # interno, sem referência a telas, botões ou navegação.

  Scenario: Listagem prioriza reservas de docentes
    Given Erick Teste está autenticado como administrador
    And existe a reserva "001" associada ao papel "discente"
    And existe a reserva "002" associada ao papel "docente"
    When Erick consulta a listagem de reservas
    Then a reserva "002" aparece antes da reserva "001"
    And o status de ambas permanece "pending"

  Scenario: Confirmar uma reserva pendente
    Given Erick Teste está autenticado como administrador
    And existe a reserva "105" para a sala "Lab 1" com status "pending"
    When Erick solicita a confirmação da reserva "105"
    Then o status da reserva "105" passa a ser "confirmed"
    And o serviço retorna a mensagem "Reserva confirmada com sucesso"

  Scenario: Negar uma reserva pendente sem justificativa
    Given Erick Teste está autenticado como administrador
    And existe a reserva "106" para a sala "Auditorio" com status "pending"
    When Erick solicita a negação da reserva "106" sem informar justificativa
    Then o status da reserva "106" passa a ser "denied"
    And o serviço retorna a mensagem "Reserva negada com sucesso"

  Scenario: Reserva já decidida é imutável
    Given Erick Teste está autenticado como administrador
    And existe a reserva "107" para a sala "Grad 3" com status "confirmed"
    When Erick solicita a confirmação da reserva "107"
    Then o serviço rejeita a operação com a mensagem "Reserva já decidida não pode ser alterada"
    And o status da reserva "107" permanece "confirmed"

  Scenario: Serviço expõe ao administrador somente as ações de confirmar e negar
    Given Erick Teste está autenticado como administrador
    And existe a reserva "108" criada por "Professor Carlos" para a sala "Grad 4" com status "pending"
    When Erick consulta o detalhe da reserva "108"
    Then o serviço informa as ações permitidas como "confirm,deny"
    And o serviço não expõe operação para alterar os dados da reserva "108"
