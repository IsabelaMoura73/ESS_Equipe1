Feature: Efetuar reserva e manutencao de reservas efetuadas usuario
  Como usuario autenticado do sistema Salla
  Quero criar, editar e cancelar reservas de salas
  Para garantir que terei acesso ao espaco no horario desejado

  #CENARIOS DE CRIACAO DE RESERVA

  Scenario: Realizar reserva de sala com sucesso
    Given o sistema nao tem nenhuma reserva confirmada da sala "D005" das "2030-06-01T08:00:00" as "2030-06-01T10:00:00"
    And existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    When o usuario Neymar tenta reservar a sala "D005" das "2030-06-01T08:00:00" as "2030-06-01T10:00:00"
    Then o sistema armazena a reserva com status "pending"

  Scenario: Tentar reservar sala com sobreposicao de horario
    Given o sistema possui uma reserva confirmada da sala "D005" das "2030-06-02T09:00:00" as "2030-06-02T11:00:00"
    And existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    When o usuario Neymar tenta reservar a sala "D005" das "2030-06-02T08:00:00" as "2030-06-02T10:00:00"
    Then o servidor retorna um erro informando que a sala ja esta reservada neste periodo

  Scenario: Usuario tenta criar duas reservas no mesmo horario em salas diferentes
    Given existe um usuario autenicado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente da sala "D005" das "2030-06-09T08:00:00" as "2030-06-09T10:00:00" para Neymar
    When o usuario Neymar tenta reservar a sala "E101" das "2030-06-09T08:00:00" as "2030-06-09T10:00:00"
    Then o servidor retorna um erro informando que o usuario ja possui uma reserva neste horario

  Scenario: Tentar reservar com usuario nao logado no sistema
    Given a sala "D005" existe no sistema
    When um usuario nao autenticado tenta reservar a sala "D005" das "2030-06-16T08:00:00" as "2030-06-16T10:00:00"
    Then o servidor retorna um erro de autenticacao

  Scenario: Tentar reservar sala inexistente
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    When o usuario Neymar tenta reservar a sala "INEXISTENTE" das "2030-06-13T08:00:00" as "2030-06-13T10:00:00"
    Then o servidor retorna um erro informando que a sala nao foi encontrada

  Scenario: Tentar reservar sala em manutencao
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema tem a sala "D005" com status de manutencao "Sim"
    When o usuario Neymar tenta reservar a sala "D005" das "2030-06-14T08:00:00" as "2030-06-14T10:00:00"
    Then o servidor retorna um erro informando que a sala esta em manutencao

  Scenario: Tentar reservar sala com manutencao agendada
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema tem a sala "D005" com manutencao agendada de "2030-06-15" a "2030-06-16"
    When o usuario Neymar tenta reservar a sala "D005" das "2030-06-15T08:00:00" as "2030-06-15T10:00:00"
    Then o servidor retorna um erro informando que a sala esta em manutencao

  Scenario: Tentar criar reserva com horario de inicio no passado
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    When o usuario Neymar tenta reservar a sala "D005" das "2020-01-01T08:00:00" as "2020-01-01T10:00:00"
    Then o servidor retorna um erro informando que o horario de inicio esta no passado

  Scenario: Tentar criar reserva com horario de fim antes do horario de inicio
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    When o usuario Neymar tenta reservar a sala "D005" das "2030-06-20T10:00:00" as "2030-06-20T08:00:00"
    Then o servidor retorna um erro informando que o horario de fim deve ser posterior ao inicio

  #CENARIOS DE EDICAO DE RESERVA

  Scenario: Editar sala e horario de fim de uma reserva pendente com sucesso
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-06T10:00:00" as "2030-06-06T12:00:00" para Neymar
    When o usuario Neymar tenta editar a reserva de ID 1 alterando sala para "E101" e horario de fim para "2030-06-06T13:00:00"
    Then o sistema atualiza a sala da reserva para "E101"
    And o sistema atualiza o horario de fim da reserva para "2030-06-06T13:00:00"

  Scenario: Tentar editar reserva ja confirmada
    Given existe um usuario com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva de ID 1 com status "confirmed" da sala "D005" das "2030-06-07T08:00:00" as "2030-06-07T10:00:00" para Neymar
    When o usuario Neymar tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-07T11:00:00"
    Then o servidor retorna um erro informando que so e possivel editar reservas pendentes

  Scenario: Tentar editar reserva de outro usuario
    Given existe um usuario com nome "Neymar" CPF "12345678901" e senha "12345678"
    And existe um usuario com nome "Messi" CPF "98765432100" e senha "87654321"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-21T08:00:00" as "2030-06-21T10:00:00" para Messi
    When o usuario Neymar tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-21T11:00:00"
    Then o servidor retorna um erro informando que o usuario nao e dono da reserva

  Scenario: Tentar editar reserva para sala em manutencao
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-22T08:00:00" as "2030-06-22T10:00:00" para Neymar
    And o sistema tem a sala "E101" com status de manutencao "Sim"
    When o usuario Neymar tenta editar a reserva de ID 1 alterando sala para "E101"
    Then o servidor retorna um erro informando que a sala esta em manutencao

  Scenario: Tentar editar reserva para sala inexistente
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-23T08:00:00" as "2030-06-23T10:00:00" para Neymar
    When o usuario Neymar tenta editar a reserva de ID 1 alterando sala para "INEXISTENTE"
    Then o servidor retorna um erro informando que a sala nao foi encontrada

  Scenario: Tentar editar reserva gerando conflito de horario com reserva confirmada
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-24T08:00:00" as "2030-06-24T10:00:00" para Neymar
    And o sistema possui uma reserva confirmada da sala "D005" das "2030-06-24T09:00:00" as "2030-06-24T12:00:00"
    When o usuario Neymar tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-24T11:00:00"
    Then o servidor retorna um erro informando que a sala ja esta reservada neste periodo

  Scenario: Tentar editar reserva gerando conflito de horario do proprio usuario
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-25T08:00:00" as "2030-06-25T10:00:00" para Neymar
    And o sistema possui uma reserva pendente fixa da sala "E101" das "2030-06-25T11:00:00" as "2030-06-25T13:00:00" para Neymar
    When o usuario Neymar tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-25T12:00:00"
    Then o servidor retorna um erro informando que o usuario ja possui uma reserva neste horario

  #CENARIOS DE CANCELAMENTO DE RESERVA

  Scenario: Cancelar reserva pendente
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-04T08:00:00" as "2030-06-04T10:00:00" para Neymar
    When o usuario Neymar tenta cancelar a reserva de ID 1
    Then o sistema marca a reserva com status "denied"

  Scenario: Tentar cancelar reserva ja negada
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And o sistema possui uma reserva de ID 1 com status "denied" da sala "D005" das "2030-06-08T08:00:00" as "2030-06-08T10:00:00" para Neymar
    When o usuario Neymar tenta cancelar a reserva de ID 1
    Then o servidor retorna um erro informando que so e possivel editar reservas pendentes

  Scenario: Tentar cancelar reserva de outro usuario
    Given existe um usuario autenticado com nome "Neymar" CPF "12345678901" e senha "12345678"
    And existe um usuario com nome "Messi" CPF "98765432100" e senha "87654321"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-18T08:00:00" as "2030-06-18T10:00:00" para Messi
    When o usuario Neymar tenta cancelar a reserva de ID 1
    Then o servidor retorna um erro informando que o usuario nao e dono da reserva
