Feature: maintenance
  As a teacher at an institution
  I want to add, remove, or edit room maintenance requests
  so that I can report and follow up on room issues that affect my classes

  Scenario: Criar solicitação de manutenção com sucesso
    Given o professor está autenticado
    And nenhuma solicitação sua existe para a sala "Grad 2"
    When o professor informa "Grad 2" no campo "Nome da sala"
    And o professor informa "Ar-condicionado com defeito" no campo "Descrição"
    And o professor submete a solicitação
    Then o sistema registra a solicitação com status "Pendente" associada ao professor autenticado
    And o sistema retorna confirmação de sucesso

  Scenario: Falha ao criar solicitação para sala com manutenção pendente
    Given o professor está autenticado
    And já existe uma solicitação com status "Pendente" para a sala "Grad 2" associada ao professor autenticado
    When o professor informa "Grad 2" no campo "Nome da sala"
    And o professor informa "Ar-condicionado com defeito" no campo "Descrição"
    And o professor submete a solicitação
    Then o sistema não registra a solicitação
    And o sistema retorna mensagem de erro "Já existe uma solicitação pendente para esta sala"

  Scenario: Falha ao criar solicitação com campo obrigatório vazio
    Given o professor está autenticado
    When o professor informa "Grad 2" no campo "Nome da sala", mas sem descrição
    And o professor submete a solicitação
    Then o sistema não registra a solicitação
    And o sistema exibe a mensagem de erro "O campo Descrição é obrigatório"

  Scenario: Excluir solicitação com status pendente
    Given o professor está autenticado
    And o professor possui uma solicitação com status "Pendente" em seu nome
    When o professor requisita a exclusão dessa solicitação pelo seu ID
    Then a solicitação não está mais visível para o professor
    And o sistema retorna confirmação de exclusão

  Scenario: Editar descrição de solicitação com status pendente
    Given o professor está autenticado
    And o professor possui uma solicitação com status "Pendente" com a descrição "Ar-condicionado com defeito"
    When o professor edita a solicitação pelo seu ID informando "Ar-condicionado barulhento e com defeito" no campo "Descrição"
    And o professor submete a edição
    Then a solicitação passa a exibir a descrição "Ar-condicionado barulhento e com defeito"
    And o sistema retorna confirmação de edição 