Feature: Gerenciamento de usuarios
  Como usuario do sistema Salla
  Quero me cadastrar, autenticar e gerenciar minha conta
  Para acessar o sistema de reservas de salas e equipamentos

  #CENARIOS DE CADASTRO

  Scenario: Cadastro de discente realizado com sucesso
    Given o sistema nao tem um usuario com CPF "11122233344"
    When uma requisicao "POST" for enviada para "/users" com nome "John Logan", CPF "11122233344", tipo "discente", matricula "20230001", curso "Computacao" e senha "senha123"
    Then o status da resposta deve ser "201"
    And o JSON da resposta deve conter CPF "11122233344", nome "John Logan", tipo "discente" e status "ativo"

  Scenario: Cadastro de docente realizado com sucesso
    Given o sistema nao tem um usuario com CPF "55566677788"
    When uma requisicao "POST" for enviada para "/users" com nome "Pedro Mota", CPF "55566677788", tipo "docente", siape "1234567" e senha "senha123"
    Then o status da resposta deve ser "201"
    And o JSON da resposta deve conter CPF "55566677788", nome "Pedro Mota" e tipo "docente"

  Scenario: Tentativa de cadastro com CPF ja existente
    Given o sistema ja tem um usuario com CPF "11122233344"
    When uma requisicao "POST" for enviada para "/users" com nome "Fake John", CPF "11122233344", tipo "discente", matricula "20230002", curso "Direito" e senha "senha123"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter uma mensagem informando que o CPF ja esta cadastrado
    And uma requisicao "GET" para "/users?cpf=11122233344" retorna exatamente 1 usuario

  Scenario: Tentativa de cadastro de docente sem SIAPE
    Given o sistema nao tem um usuario com CPF "99988877766"
    When uma requisicao "POST" for enviada para "/users" com nome "Dr Who", CPF "99988877766", tipo "docente", sem siape e senha "senha123"
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter uma mensagem de erro de validacao

  Scenario: Tentativa de cadastro de discente sem matricula
    Given o sistema nao tem um usuario com CPF "12312312300"
    When uma requisicao "POST" for enviada para "/users" com nome "Discente Sem Matricula", CPF "12312312300", tipo "discente", curso "Computacao", sem matricula e senha "senha123"
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter uma mensagem de erro de validacao

  Scenario: Tentativa de cadastro com CPF invalido
    Given o sistema nao tem um usuario com CPF "000"
    When uma requisicao "POST" for enviada para "/users" com nome "CPF Invalido", CPF "000", tipo "discente", matricula "20230001", curso "Computacao" e senha "senha123"
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter uma mensagem de erro de validacao

  Scenario: Tentativa de cadastro com senha muito curta
    Given o sistema nao tem um usuario com CPF "44455566677"
    When uma requisicao "POST" for enviada para "/users" com nome "Senha Curta", CPF "44455566677", tipo "discente", matricula "20230001", curso "Computacao" e senha "abc"
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter uma mensagem de erro de validacao

  #CENARIOS DE LOGIN

  Scenario: Login realizado com sucesso
    Given o sistema tem um usuario ativo com CPF "11122233344" e senha "senha123"
    When uma requisicao "POST" for enviada para "/users/login" com CPF "11122233344" e senha "senha123"
    Then o status da resposta deve ser "200"
    And o JSON da resposta deve conter CPF "11122233344" e nome "John Logan"

  Scenario: Tentativa de login com senha incorreta
    Given o sistema tem um usuario ativo com CPF "11122233344" e senha "senha123"
    When uma requisicao "POST" for enviada para "/users/login" com CPF "11122233344" e senha "senhaerrada"
    Then o status da resposta deve ser "401"
    And o JSON da resposta deve conter uma mensagem informando CPF ou senha invalidos

  Scenario: Tentativa de login com CPF nao cadastrado
    Given o sistema nao tem um usuario com CPF "00000000000"
    When uma requisicao "POST" for enviada para "/users/login" com CPF "00000000000" e senha "senha123"
    Then o status da resposta deve ser "401"
    And o JSON da resposta deve conter uma mensagem informando CPF ou senha invalidos

  Scenario: Tentativa de login com conta desativada
    Given o sistema tem um usuario desativado com CPF "11122233344" e senha "senha123"
    When uma requisicao "POST" for enviada para "/users/login" com CPF "11122233344" e senha "senha123"
    Then o status da resposta deve ser "403"
    And o JSON da resposta deve conter uma mensagem informando que a conta esta desativada

  #CENARIOS DE EDITAR NOME OU SENHA

  Scenario: Alteracao de nome realizada com sucesso
    Given o sistema tem um usuario ativo com CPF "11122233344", nome "John Logan" e senha "senha123"
    When uma requisicao "PATCH" for enviada para "/users/11122233344" com o novo nome "John Logan Moura"
    Then o status da resposta deve ser "200"
    And o JSON da resposta deve conter CPF "11122233344" e nome "John Logan Moura"

  Scenario: Alteracao de senha realizada com sucesso
    Given o sistema tem um usuario ativo com CPF "11122233344" e senha "senha123"
    When uma requisicao "PATCH" for enviada para "/users/11122233344" com a nova senha "novasenha456"
    Then o status da resposta deve ser "200"
    And uma requisicao "POST" para "/users/login" com CPF "11122233344" e senha "novasenha456" retorna status "200"
    And uma requisicao "POST" para "/users/login" com CPF "11122233344" e senha "senha123" retorna status "401"

  Scenario: Tentativa de atualizacao com senha nova muito curta
    Given o sistema tem um usuario ativo com CPF "11122233344" e senha "senha123"
    When uma requisicao "PATCH" for enviada para "/users/11122233344" com a nova senha "abc"
    Then o status da resposta deve ser "422"
    And o JSON da resposta deve conter uma mensagem de erro de validacao
    And uma requisicao "POST" para "/users/login" com CPF "11122233344" e senha "senha123" retorna status "200"

  #CENARIOS DE DESATIVACAO

  Scenario: Desativacao de conta com reservas pendentes e confirmadas
    Given o sistema tem um usuario ativo com CPF "11122233344"
    And o sistema tem uma reserva com status "pending" associada ao usuario com CPF "11122233344"
    And o sistema tem uma reserva com status "confirmed" associada ao usuario com CPF "11122233344"
    When uma requisicao "PATCH" for enviada para "/users/11122233344/deactivate"
    Then o status da resposta deve ser "200"
    And o JSON da resposta deve conter CPF "11122233344" e status "desativado"
    And o sistema deve ter todas as reservas do usuario com CPF "11122233344" com status "denied"

  Scenario: Desativacao de conta sem reservas ativas
    Given o sistema tem um usuario ativo com CPF "11122233344"
    And o sistema nao tem reservas associadas ao usuario com CPF "11122233344"
    When uma requisicao "PATCH" for enviada para "/users/11122233344/deactivate"
    Then o status da resposta deve ser "200"
    And o JSON da resposta deve conter CPF "11122233344" e status "desativado"

  Scenario: Tentativa de desativar conta ja desativada
    Given o sistema tem um usuario desativado com CPF "11122233344"
    When uma requisicao "PATCH" for enviada para "/users/11122233344/deactivate"
    Then o status da resposta deve ser "400"
    And o JSON da resposta deve conter uma mensagem informando que a conta ja esta desativada
