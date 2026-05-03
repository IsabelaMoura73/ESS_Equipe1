Feature: Confirmação e Negação de Solicitações de Manutenção
  As um administrador do sistema
  I want to confirmar ou negar solicitações de manutenção de salas
  So that eu possa gerenciar adequadamente o estado e a disponibilidade das salas

  Scenario: Visualizar detalhes de uma solicitação de manutenção pendente
    Given eu estou logado como administrador
    When eu acesso a página de visualização de solicitações de manutenção
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala A"
    And eu consigo visualizar a solicitação

  Scenario: Tentativa de acesso à página de solicitações de manutenção por usuário 
    Given eu estou logado como um usuário
    When eu tento acessar a página de visualização de solicitações de manutenção
    And eu vejo a mensagem "Acesso negado. Você não tem permissão para acessar esta página."

  Scenario: Confirmar solicitação de manutenção com sucesso
    Given eu estou logado como administrador
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala B"
    And a "Sala B" não possui reservas com status "Confirmada" na data atual
    When eu seleciono a opção de confirmar a solicitação
    And eu preencho o campo "Data de fim da manutenção" com "XX/XX/XXXX"
    And eu clico em "Confirmar manutenção"
    Then o status da solicitação é atualizado para "Confirmada"
    And a "Sala B" entra em manutenção com início na data atual e fim em "XX/XX/XXXX"

  Scenario: Negar solicitação de manutenção
    Given eu estou logado como administrador
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala C"
    When eu seleciono a opção de negar a solicitação
    Then o status da solicitação é atualizado para "Negada"
    And a "Sala C" permanece disponível para reservas

  Scenario: Confirmar manutenção e negar reservas pendentes automaticamente
    Given eu estou logado como administrador
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala D"
    And a "Sala D" não possui reservas com status "Confirmada" na data atual
    When eu seleciono a opção de confirmar a solicitação
    And eu preencho o campo "Data de fim da manutenção" com "XX/XX/XXXX"
    And eu clico em "Confirmar manutenção"
    And a "Sala D" possui reservas com status "Pendente" dentro do período de manutenção
    Then o status da solicitação é atualizado para "Confirmada"
    And todas as reservas com status "Pendente" da "Sala D" dentro do período de manutenção são automaticamente alteradas para "Negada"

  Scenario: Impedir confirmação de manutenção com reservas confirmadas no período
    Given eu estou logado como administrador
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala E"
    And a "Sala E" não possui reservas com status "Confirmada" na data atual
    When eu seleciono a opção de confirmar a solicitação
    And eu preencho o campo "Data de fim da manutenção" com "XX/XX/XXXX"
    And eu clico em "Confirmar manutenção"
    Then o sistema impede a confirmação da manutenção
    And eu vejo a mensagem "Não é possível confirmar a manutenção. Existem reservas confirmadas para esta sala no período selecionado."
    And o status da solicitação permanece "Pendente"

  Scenario: Tentar confirmar manutenção sem informar data de fim
    Given eu estou logado como administrador
    And existe uma solicitação de manutenção com status "Pendente" para a "Sala G"
    When eu seleciono a opção de confirmar a solicitação
    And eu deixo o campo "Data de fim da manutenção" vazio
    And eu clico em "Confirmar manutenção"
    Then eu vejo a mensagem "O campo Data de fim da manutenção é obrigatório."
    And o status da solicitação permanece "Pendente"
