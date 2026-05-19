Feature: Room Service - Gerenciar salas

Scenario: Criar sala com dados válidos
Given nenhuma sala com nome "D005" existe no banco
And o corpo da requisição tem nome "D005", capacidade "80", descrição "sala de reunião", computadores "40" e status de manutenção "Não"
When uma requisição "POST" é enviada para "/api/rooms/" com os dados da sala
Then o status da resposta deve ser "201"
And a sala deve ser armazenada com name "D005" como primary key
And a sala deve ter "created_at" preenchido automaticamente

Scenario: Rejeitar criação de sala com dados incompletos
Given o corpo da requisição faltando o campo "capacity"
And o corpo da requisição tem nome "D005", descrição "sala", computadores "40"
When uma requisição "POST" é enviada para "/api/rooms/"
Then o status da resposta deve ser "422"
And a mensagem de resposta deve conter "capacity"

Scenario: Rejeitar computadores negativos
Given o corpo da requisição tem nome "D005", capacidade "80", computadores "-1"
When uma requisição "POST" é enviada para "/api/rooms/"
Then o status da resposta deve ser "422"

Scenario: Rejeitar descrição maior que 500 caracteres
Given o corpo da requisição tem nome "D005", capacidade "80", descrição com mais de 500 caracteres
When uma requisição "POST" é enviada para "/api/rooms/"
Then o status da resposta deve ser "422"

Scenario: Rejeitar criação de sala duplicada
Given uma sala "D005" com capacidade "80" e computadores "40" já existe no banco
And o corpo da requisição tem nome "D005", capacidade "100", computadores "50"
When uma requisição "POST" é enviada para "/api/rooms/"
Then o status da resposta deve ser "409"
And a mensagem de resposta deve ser "Já existe uma sala com o nome 'D005'"
And a sala original mantém capacidade "80" e computadores "40"

Scenario: Deletar sala disponível
Given uma sala "D005" com is_reserved "false" existe
When uma requisição "DELETE" é enviada para "/api/rooms/D005"
Then o status da resposta deve ser "204"
And a resposta não contém corpo
And a sala "D005" não existe mais no banco

Scenario: Rejeitar deleção de sala reservada
Given uma sala "D005" com is_reserved "true" existe
When uma requisição "DELETE" é enviada para "/api/rooms/D005"
Then o status da resposta deve ser "400"
And a mensagem de resposta deve conter "Não é possível remover a sala que está reservada"
And a sala "D005" ainda existe no banco