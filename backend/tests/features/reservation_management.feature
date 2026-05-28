Feature: Efetuar reserva e manutencao de reservas efetuadas usuario
  Como usuario autenticado do sistema Salla
  Quero criar, editar e cancelar reservas de salas
  Para garantir que terei acesso ao espaco no horario desejado

  #CENARIOS DE CRIACAO DE RESERVA

  Scenario: Realizar reserva de sala com sucesso
    Given o sistema nao tem nenhuma reserva confirmada da sala "D005" das "2030-06-01T08:00:00" as "2030-06-01T10:00:00"
    And o sistema tem um usuario com CPF "12345678901"
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-01T08:00:00" as "2030-06-01T10:00:00"
    Then o sistema armazena a reserva com status "pending"

  Scenario: Tentar reservar sala com sobreposicao de horario
    Given o sistema possui uma reserva confirmada da sala "D005" das "2030-06-02T09:00:00" as "2030-06-02T11:00:00"
    And o sistema tem um usuario com CPF "12345678901"
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-02T08:00:00" as "2030-06-02T10:00:00"
    Then o servidor retorna um erro informando que a sala ja esta reservada neste periodo

  Scenario: Usuario tenta criar duas reservas no mesmo horario em salas diferentes
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva pendente da sala "D005" das "2030-06-09T08:00:00" as "2030-06-09T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta reservar a sala "E101" das "2030-06-09T08:00:00" as "2030-06-09T10:00:00"
    Then o servidor retorna um erro informando que o usuario ja possui uma reserva neste horario

  Scenario: Duas reservas pending da mesma sala e horario de usuarios diferentes coexistem
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema tem um usuario com CPF "98765432100"
    And o sistema possui uma reserva pendente da sala "D005" das "2030-06-10T08:00:00" as "2030-06-10T10:00:00" para o CPF "98765432100"
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-10T08:00:00" as "2030-06-10T10:00:00"
    Then o sistema armazena a reserva com status "pending" e CPF "12345678901"

  Scenario: Tentar reservar com CPF nao cadastrado no sistema
    Given o sistema nao possui um usuario com CPF "99999999999"
    When o usuario com CPF "99999999999" tenta reservar a sala "D005" das "2030-06-11T08:00:00" as "2030-06-11T10:00:00"
    Then o servidor retorna um erro informando que o usuario nao foi encontrado

  Scenario: Tentar reservar com conta desativada
    Given o sistema tem um usuario com CPF "12345678901"
    And a conta do usuario com CPF "12345678901" esta desativada
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-12T08:00:00" as "2030-06-12T10:00:00"
    Then o servidor retorna um erro informando que a conta esta desativada

  Scenario: Tentar reservar sala inexistente
    Given o sistema tem um usuario com CPF "12345678901"
    When o usuario com CPF "12345678901" tenta reservar a sala "INEXISTENTE" das "2030-06-13T08:00:00" as "2030-06-13T10:00:00"
    Then o servidor retorna um erro informando que a sala nao foi encontrada

  Scenario: Tentar reservar sala em manutencao
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema tem a sala "D005" com status de manutencao "Sim"
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-14T08:00:00" as "2030-06-14T10:00:00"
    Then o servidor retorna um erro informando que a sala esta em manutencao

  Scenario: Tentar reservar sala com manutencao agendada
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema tem a sala "D005" com status de manutencao "Agendada"
    When o usuario com CPF "12345678901" tenta reservar a sala "D005" das "2030-06-15T08:00:00" as "2030-06-15T10:00:00"
    Then o servidor retorna um erro informando que a sala esta em manutencao

  #CENARIOS DE EDICAO DE RESERVA

  Scenario: Editar horario de fim de uma reserva pendente com sucesso
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-03T08:00:00" as "2030-06-03T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-03T11:00:00"
    Then o sistema atualiza o horario de fim da reserva para "2030-06-03T11:00:00"
    And o status da reserva permanece "pending"

  Scenario: Editar sala de uma reserva pendente com sucesso
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-17T08:00:00" as "2030-06-17T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta editar a reserva de ID 1 alterando sala para "E101"
    Then o sistema atualiza a sala da reserva de ID 1 para "E101"

  Scenario: Editar sala e horario de fim de uma reserva pendente com sucesso
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-06T10:00:00" as "2030-06-06T12:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta editar a reserva de ID 1 alterando sala para "E101" e horario de fim para "2030-06-06T13:00:00"
    Then o sistema atualiza a sala da reserva para "E101"
    And o sistema atualiza o horario de fim da reserva para "2030-06-06T13:00:00"

  Scenario: Tentar editar reserva ja confirmada
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva de ID 1 com status "confirmed" da sala "D005" das "2030-06-07T08:00:00" as "2030-06-07T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta editar a reserva de ID 1 alterando horario de fim para "2030-06-07T11:00:00"
    Then o servidor retorna um erro informando que so e possivel editar reservas pendentes

  #CENARIOS DE CANCELAMENTO DE RESERVA

  Scenario: Cancelar reserva pendente
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-04T08:00:00" as "2030-06-04T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta cancelar a reserva de ID 1
    Then o sistema marca a reserva com status "denied"

  Scenario: Tentar cancelar reserva ja negada
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema possui uma reserva de ID 1 com status "denied" da sala "D005" das "2030-06-08T08:00:00" as "2030-06-08T10:00:00" para o CPF "12345678901"
    When o usuario com CPF "12345678901" tenta cancelar a reserva de ID 1
    Then o servidor retorna um erro informando que so e possivel editar reservas pendentes

  Scenario: Tentar cancelar reserva de outro usuario
    Given o sistema tem um usuario com CPF "12345678901"
    And o sistema tem um usuario com CPF "98765432100"
    And o sistema possui uma reserva pendente de ID 1 da sala "D005" das "2030-06-18T08:00:00" as "2030-06-18T10:00:00" para o CPF "98765432100"
    When o usuario com CPF "12345678901" tenta cancelar a reserva de ID 1
    Then o servidor retorna um erro informando que o usuario nao e dono da reserva
