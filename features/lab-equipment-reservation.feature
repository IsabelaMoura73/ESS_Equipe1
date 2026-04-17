Feature: Lab equipment reservation

  As an enrolled student
  I want to reserve computers in a laboratory room
  So that I can guarantee access to the equipment at the desired time

  Scenario: Successful equipment reservation
    Given I am logged into the system as student "Vitoria"
    And I am on the "New Reservation" page
    And the room "Lab A" is available
    When I fill in the room name with "Lab A"
    And I fill in the number of computers with "3"
    And I fill in the start time with "10/04/2026 08:00"
    And I fill in the end time with "10/04/2026 10:00"
    And I click on "Confirm"
    Then I see the message "Reservation sent successfully"
    And the reservation is created with status "Pending"

  Scenario: Attempt to reserve equipment in a room under maintenance
    Given I am logged into the system as student "Vitoria"
    And I am on the "New Reservation" page
    And the room "Lab B" is under maintenance
    When I fill in the room name with "Lab B"
    And I fill in the number of computers with "2"
    And I fill in the start time with "10/04/2026 14:00"
    And I fill in the end time with "10/04/2026 16:00"
    And I click on "Confirm"
    Then I see the error message "Room under maintenance. Reservation not allowed"
    And no reservation is created