Feature: maintenance
  As a teacher at an institution
  I want to add, remove, or edit room maintenance requests
  so that I can report and follow up on room issues that affect my classes

  Scenario: Criar solicitação de manutenção com sucesso
    Given o sistema não possui solicitação pendente do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    Then o sistema registra a solicitação com status "pending"
    And o sistema retorna confirmação de sucesso

  Scenario: Falha ao criar solicitação para sala com solicitação pendente existente
    Given já existe uma solicitação com status "pending" do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "Já existe uma solicitação pendente para esta sala"

  Scenario: Falha ao criar solicitação com campo descrição vazio
    Given o sistema não possui solicitação pendente do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" sem descrição
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "O campo Descrição é obrigatório"

  Scenario: Falha ao criar solicitação com descrição excessivamente longa
    Given o sistema não possui solicitação pendente do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição de 501 caracteres
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "Descrição muito longa"

  Scenario: Falha ao criar solicitação para sala inexistente
    Given o sistema não possui nenhuma sala com nome "Sala Inexistente"
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Sala Inexistente" com descrição "Problema qualquer"
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "Sala não encontrada"

  Scenario: Falha ao criar solicitação para sala em manutenção
    Given a sala "Grad 2" está em manutenção no sistema
    When o sistema recebe uma solicitação do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "Sala em manutenção"

  Scenario: Excluir solicitação com status pendente
    Given o sistema possui uma solicitação com status "pending" do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma requisição de exclusão dessa solicitação pelo seu ID
    Then o sistema remove a solicitação com sucesso
    And o sistema não retorna mais essa solicitação para o professor "Breno Miranda" com CPF "11111111111"

  Scenario: Falha ao excluir solicitação já confirmada
    Given o sistema possui uma solicitação com status "confirmed" do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2"
    When o sistema recebe uma requisição de exclusão dessa solicitação pelo seu ID
    Then o sistema não remove a solicitação
    And o sistema retorna o erro "Só é possível excluir solicitações pendentes"

  Scenario: Editar descrição de solicitação com status pendente
    Given o sistema possui uma solicitação com status "pending" do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    When o sistema recebe uma requisição de edição dessa solicitação pelo seu ID com descrição "Ar-condicionado barulhento e com defeito"
    Then o sistema atualiza a descrição para "Ar-condicionado barulhento e com defeito"
    And o sistema retorna confirmação de edição

  Scenario: Falha ao editar solicitação já confirmada
    Given o sistema possui uma solicitação com status "confirmed" do professor "Breno Miranda" com CPF "11111111111" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    When o sistema recebe uma requisição de edição dessa solicitação pelo seu ID com descrição "Ar-condicionado barulhento e com defeito"
    Then o sistema não atualiza a solicitação
    And o sistema retorna o erro "Só é possível editar solicitações pendentes"

  Scenario: Falha ao criar solicitação por usuário não docente
    Given o sistema possui um usuário do tipo "discente" com CPF "22222222222"
    When o sistema recebe uma solicitação do CPF "22222222222" para a sala "Grad 2" com descrição "Ar-condicionado com defeito"
    Then o sistema não registra a solicitação
    And o sistema retorna o erro "Apenas docentes podem gerenciar solicitações de manutenção"