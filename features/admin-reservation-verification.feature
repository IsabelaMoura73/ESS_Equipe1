Feature: Verificação de Reservas
  As an administrador do sistema
  I want to visualizar, confirmar ou negar reservas de salas
  So that eu possa gerenciar a alocação e o estado das salas adequadamente

  Scenario: Visualização da listagem com prioridade para professores
    Given o administrador autenticado acessa a página "Visualização de Reservas"
    And o sistema possui a reserva "001" associada ao papel "Aluno"
    And o sistema possui a reserva "002" associada ao papel "Professor"
    When o sistema carrega a listagem de reservas cadastradas
    Then a reserva "002" do professor é exibida antes da reserva "001" do aluno na lista
    And o status de ambas permanece inalterado

  Scenario: Confirmar uma reserva pendente com sucesso
    Given o administrador autenticado acessa a página "Visualização de Reservas"
    And existe a reserva "105" para a sala "Lab 1" com status "Pendente"
    When o administrador clica no botão "Confirmar" para a reserva "105"
    Then o sistema atualiza o status da reserva "105" para "Confirmada" no banco de dados
    And o sistema retorna a mensagem de sucesso "Reserva confirmada com sucesso"

  Scenario: Negar uma reserva pendente sem justificativa
    Given o administrador autenticado acessa a página "Visualização de Reservas"
    And existe a reserva "106" para a sala "Auditorio" com status "Pendente"
    When o administrador clica no botão "Negar" para a reserva "106"
    Then o sistema atualiza o status da reserva "106" para "Negada" no banco de dados
    And o sistema não exige o preenchimento do campo "Justificativa"
    And o sistema retorna a mensagem de sucesso "Reserva negada com sucesso"

  Scenario: Tentativa de reverter uma reserva já decidida
    Given o administrador autenticado acessa a página "Visualização de Reservas"
    And existe a reserva "107" para a sala "Grad 3" com status "Confirmada"
    When o administrador visualiza os detalhes da reserva "107"
    Then o sistema exibe os botões "Confirmar" e "Negar" com o estado desabilitado
    And o sistema não permite a edição do status da reserva "107"

  Scenario: Tentativa de editar os dados de uma reserva alheia
    Given o administrador autenticado acessa os detalhes da reserva "108"
    And a reserva "108" foi criada pelo usuário "Professor Carlos" para a sala "Grad 4"
    When o administrador tenta alterar o valor do campo "Nome da sala"
    Then o campo "Nome da sala" permanece no modo somente leitura
    And o sistema apenas habilita ações de "Confirmar" ou "Negar" para o administrador