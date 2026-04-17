
Scenario: Criar Sala
Given eu estou logado como administrador com o usuário “Ana” com CPF “111111” 
And eu estou na tela de salas cadastradas
And a sala de nome “D005” não aparece na lista de salas cadastradas
When eu seleciono a opção “cadastrar sala”
And tento cadastrar a sala “D005” com capacidade “80”, descrição com “sala de reunião”, número de computadores “40” e status de manutenção “Não”
Then eu vejo uma mensagem de confirmação de cadastro de sala 
And eu ainda estou na tela de salas cadastradas
And eu vejo a sala “D005” na lista de salas cadastradas

Scenario: Remover Sala
Given eu estou logado como administrador com o usuário “Ana” com CPF “111111” 
And eu estou na tela de salas cadastradas
And eu vejo a sala “D005” na lista de salas cadastradas
When eu seleciono a opção “remover sala” da sala “D005”
And confirmo que realmente quero remover a sala “D005”
Then eu vejo uma mensagem de confirmação de remoção de sala
And eu ainda estou na tela de salas cadastradas
And eu não vejo a sala “D005” na lista de salas cadastradas
