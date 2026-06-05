Feature: Manutenção de salas — Interface do professor
  As a teacher at an institution
  I want to add, remove, or edit room maintenance requests
  so that I can report and follow up on room issues that affect my classes

  Scenario: Criar solicitação de manutenção com sucesso
    Given o professor "Breno Miranda" está autenticado na aplicação
    And nenhuma solicitação existe para a sala "D005"
    When o professor seleciona a sala "D005" no campo "Sala"
    And o professor preenche "Ar-condicionado com defeito" no campo "Descrição"
    And o professor clica no botão "Enviar solicitação"
    Then a tabela "Minhas Solicitações" exibe uma linha com a sala "D005" e status "Pendente"
    And a mensagem de sucesso "Solicitação criada com sucesso" é exibida na tela

  Scenario: Falha ao criar solicitação para sala com solicitação pendente existente
    Given o professor "Breno Miranda" está autenticado na aplicação
    And já existe uma solicitação com status "Pendente" para a sala "D005"
    When o professor seleciona a sala "D005" no campo "Sala"
    And o professor preenche "Ar-condicionado com defeito" no campo "Descrição"
    And o professor clica no botão "Enviar solicitação"
    Then a mensagem de erro "Já existe uma solicitação pendente para esta sala" é exibida na tela
    And a tabela "Minhas Solicitações" não exibe nova linha duplicada para a sala "D005"

  Scenario: Falha ao criar solicitação com campo obrigatório vazio
    Given o professor "Breno Miranda" está autenticado na aplicação
    When o professor seleciona a sala "D005" no campo "Sala"
    And o professor não preenche o campo "Descrição"
    And o professor clica no botão "Enviar solicitação"
    Then o formulário não é submetido
    And o campo "Descrição" exibe indicação de campo obrigatório

  Scenario: Falha ao criar solicitação com descrição excessivamente longa
    Given o professor "Breno Miranda" está autenticado na aplicação
    When o professor seleciona a sala "D005" no campo "Sala"
    And o professor preenche uma descrição com 501 caracteres no campo "Descrição"
    And o professor clica no botão "Enviar solicitação"
    Then a mensagem de erro "Descrição muito longa" é exibida na tela
    And a tabela "Minhas Solicitações" não exibe nova linha para a sala "D005"

  Scenario: Falha ao criar solicitação para sala em manutenção
    Given o professor "Breno Miranda" está autenticado na aplicação
    And a sala "D005" está em manutenção
    When o professor seleciona a sala "D005" no campo "Sala"
    And o professor preenche "Ar-condicionado com defeito" no campo "Descrição"
    And o professor clica no botão "Enviar solicitação"
    Then a mensagem de erro "Sala em manutenção" é exibida na tela

  Scenario: Excluir solicitação com status pendente
    Given o professor "Breno Miranda" está autenticado na aplicação
    And o professor possui uma solicitação com status "Pendente" para a sala "D005"
    When o professor clica no botão "Excluir" da linha correspondente à sala "D005"
    And o professor confirma a exclusão no modal de confirmação
    Then a linha da sala "D005" não aparece mais na tabela "Minhas Solicitações"
    And a mensagem de sucesso "Solicitação excluída com sucesso" é exibida na tela

  Scenario: Editar descrição de solicitação com status pendente
    Given o professor "Breno Miranda" está autenticado na aplicação
    And o professor possui uma solicitação com status "Pendente" e descrição "Ar-condicionado com defeito" para a sala "D005"
    When o professor clica no botão "Editar" da linha correspondente à sala "D005"
    And o professor limpa e preenche "Ar-condicionado barulhento e com defeito" no campo "Descrição"
    And o professor clica no botão "Salvar alterações"
    Then a linha da sala "D005" exibe a descrição "Ar-condicionado barulhento e com defeito"
    And a mensagem de sucesso "Solicitação atualizada com sucesso" é exibida na tela
