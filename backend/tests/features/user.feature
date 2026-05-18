Feature: Gerenciamento de usuarios
  Como usuario do sistema Salla
  Quero me cadastrar, autenticar e gerenciar minha conta
  Para acessar o sistema de reservas de salas e equipamentos

  #CENARIOS DE CADASTRO 

  Scenario: Cadastro de discente realizado com sucesso
    Given o sistema nao tem um usuario com CPF "11122233344"
    When eu tento cadastrar o usuario "John Logan" com CPF "11122233344", tipo "discente", matricula "20230001", curso "Computacao" e senha "senha123"
    Then o sistema armazena o usuario "John Logan" com CPF "11122233344" e tipo "discente"
    And o status do usuario "John Logan" com CPF "11122233344" e ativo

  Scenario: Cadastro de docente realizado com sucesso
    Given o sistema nao tem um usuario com CPF "55566677788"
    When eu tento cadastrar o usuario "Pedro Mota" com CPF "55566677788", tipo "docente", siape "1234567" e senha "senha123"
    Then o sistema armazena o usuario "Pedro Mota" com CPF "55566677788" e tipo "docente"

  Scenario: Tentativa de cadastro com CPF ja existente
    Given o sistema tem um usuario "John Logan" com CPF "11122233344"
    When eu tento cadastrar o usuario "Fake John" com CPF "11122233344", tipo "discente", matricula "20230002", curso "Direito" e senha "senha123"
    Then o servidor retorna um erro informando que o CPF ja esta cadastrado
    And o sistema ainda tem apenas um usuario com CPF "11122233344"

  Scenario: Tentativa de cadastro de docente sem SIAPE
    Given o sistema nao tem um usuario com CPF "99988877766"
    When eu tento cadastrar o usuario "Dr Who" com CPF "99988877766", tipo "docente", sem siape e senha "senha123"
    Then o servidor retorna um erro de validacao
    And o sistema nao tem um usuario com CPF "99988877766"

  Scenario: Tentativa de cadastro de discente sem matricula
    Given o sistema nao tem um usuario com CPF "12312312300"
    When eu tento cadastrar o usuario "Discente Sem Matricula" com CPF "12312312300", tipo "discente", curso "Computacao", sem matricula e senha "senha123"
    Then o servidor retorna um erro de validacao
    And o sistema nao tem um usuario com CPF "12312312300"

  Scenario: Tentativa de cadastro com CPF invalido
    Given o sistema nao tem um usuario com CPF "000"
    When eu tento cadastrar o usuario "CPF Invalido" com CPF "000", tipo "discente", matricula "20230001", curso "Computacao" e senha "senha123"
    Then o servidor retorna um erro de validacao
    And o sistema nao tem um usuario com CPF "000"

  Scenario: Tentativa de cadastro com senha muito curta
    Given o sistema nao tem um usuario com CPF "44455566677"
    When eu tento cadastrar o usuario "Senha Curta" com CPF "44455566677", tipo "discente", matricula "20230001", curso "Computacao" e senha "abc"
    Then o servidor retorna um erro de validacao
    And o sistema nao tem um usuario com CPF "44455566677"

  #CENARIOS DE LOGIN 

  Scenario: Login realizado com sucesso
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu realizo o login com CPF "11122233344" e senha "senha123"
    Then o servidor retorna os dados do usuario "John Logan" com CPF "11122233344"

  Scenario: Tentativa de login com senha incorreta
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu realizo o login com CPF "11122233344" e senha "senhaerrada"
    Then o servidor retorna um erro informando CPF ou senha invalidos

  Scenario: Tentativa de login com CPF nao cadastrado
    Given o sistema nao tem um usuario com CPF "00000000000"
    When eu realizo o login com CPF "00000000000" e senha "senha123"
    Then o servidor retorna um erro informando CPF ou senha invalidos

  Scenario: Tentativa de login com conta desativada
    Given o sistema tem um usuario desativado "John Logan" com CPF "11122233344" e senha "senha123"
    When eu realizo o login com CPF "11122233344" e senha "senha123"
    Then o servidor retorna um erro informando que a conta esta desativada
    And o sistema ainda tem o usuario "John Logan" com CPF "11122233344" com status desativado

  #CENARIOS DE EDITAR NOME OU SENHA

  Scenario: Alteracao de nome realizada com sucesso
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu atualizo o nome do usuario com CPF "11122233344" para "John Logan Moura"
    Then o servidor retorna os dados atualizados com nome "John Logan Moura"
    And o sistema armazena o usuario com CPF "11122233344" com nome "John Logan Moura"

  Scenario: Alteracao de senha realizada com sucesso
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu atualizo a senha do usuario com CPF "11122233344" para "novasenha456"
    Then o servidor retorna os dados do usuario com CPF "11122233344"
    And o sistema permite login com CPF "11122233344" e nova senha "novasenha456"

  Scenario: Tentativa de atualizacao com senha nova muito curta
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu tento atualizar a senha do usuario com CPF "11122233344" para "abc"
    Then o servidor retorna um erro de validacao
    And o sistema ainda permite login com CPF "11122233344" e senha original "senha123"

  #CENARIOS DE DESATIVACAO

  Scenario: Desativacao de conta com reservas pendentes e confirmadas
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    And o sistema tem uma reserva com status "pending" associada ao usuario com CPF "11122233344"
    And o sistema tem uma reserva com status "confirmed" associada ao usuario com CPF "11122233344"
    When eu solicito a desativacao da conta do usuario com CPF "11122233344"
    Then o servidor retorna os dados do usuario com CPF "11122233344" com status desativado
    And o sistema armazena o usuario com CPF "11122233344" com status desativado
    And o sistema armazena todas as reservas do usuario com CPF "11122233344" com status "denied"

  Scenario: Desativacao de conta sem reservas ativas
    Given o sistema tem um usuario ativo "John Logan" com CPF "11122233344" e senha "senha123"
    When eu solicito a desativacao da conta do usuario com CPF "11122233344"
    Then o servidor retorna os dados do usuario com CPF "11122233344" com status desativado
    And o sistema armazena o usuario com CPF "11122233344" com status desativado

  Scenario: Tentativa de desativar conta ja desativada
    Given o sistema tem um usuario desativado "John Logan" com CPF "11122233344" e senha "senha123"
    When eu solicito a desativacao da conta do usuario com CPF "11122233344"
    Then o servidor retorna um erro informando que a conta ja esta desativada
    And o sistema armazena o usuario com CPF "11122233344" com status desativado
