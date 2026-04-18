Scenario: Cadastro de usuário discente realizado com sucesso
Given eu estou na página “Cadastro de Usuário”
And o CPF "12345678900" não está cadastrado no sistema
When eu preencho “Nome” com “Kauanny Barros”
And eu preencho “CPF” com “12345678900”
And eu seleciono “Discente” como tipo de vínculo
And eu preencho “Curso” com "Engenharia da Computação”
And eu preencho “Matrícula” com “2023001234”
And eu preencho “Senha” com “senha123”
And eu clico no botão “Confirmar”
Then eu vejo uma mensagem “Usuário cadastrado com sucesso!”
And o usuário "Kauanny Barros" é cadastrado como discente no sistema

Scenario: Alteração de nome do usuário com sucesso
Given eu estou na página “Dados do Usuário”
And eu estou autenticado como o usuário “Kauanny Barros”
When eu clico no botão "Editar"
And eu altero o campo “Nome” para “Kauanny K. Barros”
And eu preencho o campo “Senha” com “senha123”
And eu clico no botão “Salvar alterações”
Then eu vejo uma mensagem “Dados atualizados com sucesso!”
And eu vejo o nome atualizado como “Kauanny K. Barros”
And o nome do usuário é atualizado para “Kauanny K. Barros” no sistema

Scenario: Desativação de conta com cancelamento de reservas
Given eu estou na página “Dados do Usuário”
And eu estou autenticado como o usuário “Kauanny Barros”
And o usuário possui reservas com status “Confirmada” e “Pendente”
When eu clico na opção “Desativar conta”
And eu confirmo a desativação
Then eu vejo a mensagem “Conta desativada com sucesso!”
And a conta do usuário está com status “Desativada”
And todas as reservas do usuário com status “Confirmada” e “Pendente” são excluídas