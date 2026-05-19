Feature: maintenance
  As a teacher at an institution
  I want to add, remove, or edit room maintenance requests
  so that I can report and follow up on room issues that affect my classes

  Scenario: Criar solicitação de manutenção com sucesso
    Given o MaintenanceService não tem uma solicitação pendente do professor "Breno Miranda" para a sala "Grad 2"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "Grad 2" e description "Ar-condicionado com defeito"
    Then o status da resposta deve ser "201"
    And o JSON da resposta deve conter status "pending", room "Grad 2" e teacher_name "Breno Miranda"

  Scenario: Falha ao criar solicitação para sala com manutenção pendente
    Given já existe uma solicitação com status "pending" do professor "Breno Miranda" para a sala "Grad 2"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "Grad 2" e description "Ar-condicionado com defeito"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter a mensagem de erro "Já existe uma solicitação pendente para esta sala"

  Scenario: Falha ao criar solicitação com campo obrigatório vazio
    Given o MaintenanceService não tem uma solicitação pendente do professor "Breno Miranda" para a sala "Grad 2"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "Grad 2" e description ""
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter a mensagem de erro "O campo Descrição é obrigatório"

  Scenario: Falha ao criar solicitação com descrição excessivamente longa
    Given o MaintenanceService não tem uma solicitação pendente do professor "Breno Miranda" para a sala "Grad 2"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "Grad 2" e description com "501" caracteres
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter a mensagem de erro "Descrição muito longa"

  Scenario: Falha ao criar solicitação para sala que não existe
    Given o MaintenanceService não tem nenhuma sala com nome "XYZABC999"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "XYZABC999" e description "Problema qualquer"
    Then o status da resposta deve ser "404"
    And o JSON da resposta deve conter a mensagem de erro "Sala não encontrada"

  Scenario: Falha ao criar solicitação para sala em manutenção
    Given a sala "Grad 2" está com maintenance_status "yes"
    When uma requisição "POST" for enviada para "/api/maintenance/" com teacher_name "Breno Miranda", room "Grad 2" e description "Ar-condicionado com defeito"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter a mensagem de erro "Sala em manutenção"

  Scenario: Excluir solicitação com status pendente
    Given existe uma solicitação com status "pending" do professor "Breno Miranda" para a sala "Grad 2" com ID conhecido
    When uma requisição "DELETE" for enviada para "/api/maintenance/{id}"
    Then o status da resposta deve ser "204"
    And o MaintenanceService não retorna mais essa solicitação para o professor "Breno Miranda"

  Scenario: Falha ao excluir solicitação já confirmada
    Given existe uma solicitação com status "confirmed" do professor "Breno Miranda" para a sala "Grad 2" com ID conhecido
    When uma requisição "DELETE" for enviada para "/api/maintenance/{id}"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter a mensagem de erro "Só é possível excluir solicitações pendentes"

  Scenario: Editar descrição de solicitação com status pendente
    Given existe uma solicitação com status "pending" do professor "Breno Miranda" para a sala "Grad 2" com description "Ar-condicionado com defeito" e ID conhecido
    When uma requisição "PUT" for enviada para "/api/maintenance/{id}" com description "Ar-condicionado barulhento e com defeito"
    Then o status da resposta deve ser "200"
    And o JSON da resposta deve conter description "Ar-condicionado barulhento e com defeito"

  Scenario: Falha ao editar solicitação já confirmada
    Given existe uma solicitação com status "confirmed" do professor "Breno Miranda" para a sala "Grad 2" com description "Ar-condicionado com defeito" e ID conhecido
    When uma requisição "PUT" for enviada para "/api/maintenance/{id}" com description "Nova descrição"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter a mensagem de erro "Só é possível editar solicitações pendentes"