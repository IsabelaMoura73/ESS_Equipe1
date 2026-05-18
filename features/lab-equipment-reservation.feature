Feature: Laboratory equipment reservation

  As an enrolled student
  I want to reserve laboratory equipment
  So that I can guarantee access to the required equipment at the desired time

  Scenario: Successful equipment reservation
    Given I am logged into the system as student "Vitoria"
    And I am on the "New Equipment Reservation" page
    And the equipment type "Desktop Computer" is available
    When I select the equipment type "Desktop Computer"
    And I fill in the quantity with "3"
    And I fill in the pickup time with "10/04/2026 08:00"
    And I fill in the return time with "10/04/2026 10:00"
    And I click on "Confirm"
    Then I see the message "Equipment reservation sent successfully"
    And the reservation is created with status "Pending"

  Scenario: Attempt to reserve equipment currently unavailable due to maintenance
    Given I am logged into the system as student "Vitoria"
    And I am on the "New Equipment Reservation" page
    And the equipment type "Projector" is under maintenance
    When I select the equipment type "Projector"
    And I fill in the quantity with "1"
    And I fill in the pickup time with "10/04/2026 14:00"
    And I fill in the return time with "10/04/2026 16:00"
    And I click on "Confirm"
    Then I see the error message "Equipment under maintenance. Reservation not allowed"
    And no reservation is created

  Scenario: Attempt to create a reservation with a time conflict for the same student
    Given I am logged into the system as student "Vitoria"
    And I already have a reservation from "10/04/2026 08:00" to "10/04/2026 10:00"
    And I am on the "New Equipment Reservation" page
    When I select the equipment type "Notebook"
    And I fill in the quantity with "1"
    And I fill in the pickup time with "10/04/2026 09:00"
    And I fill in the return time with "10/04/2026 11:00"
    And I click on "Confirm"
    Then I see the error message "You already have a reservation at this time"
    And no reservation is created

  Scenario: Cancel a pending equipment reservation
    Given I am logged into the system as student "Vitoria"
    And I have a reservation for equipment type "Desktop Computer" with status "Pending"
    And I am on the reservation details page
    When I click on "Cancel"
    Then the reservation is canceled successfully
    And the reservation no longer appears in my active reservations list

  Scenario: Successful reservation creation service scenario
    Given the student with login "Vitoria" has no active reservation from "10/04/2026 08:00" to "10/04/2026 10:00"
    And the equipment type "Desktop Computer" is available and not under maintenance
    When the system receives a reservation request with equipment type "Desktop Computer", quantity "3", pickup time "10/04/2026 08:00", and return time "10/04/2026 10:00" for the student with login "Vitoria"
    Then the system registers the reservation with status "Pending"
    And the reservation is associated with the student with login "Vitoria"
    And the stored data are equipment type "Desktop Computer", quantity 3, pickup time "10/04/2026 08:00", and return time "10/04/2026 10:00"
    And the reservation appears in the student's reservation list

  Scenario: Block reservation of equipment under maintenance
    Given the student with login "Vitoria" has no reservation from "10/04/2026 14:00" to "10/04/2026 16:00"
    And the equipment type "Projector" is currently under active maintenance
    When the system receives a reservation request with equipment type "Projector", quantity "1", pickup time "10/04/2026 14:00", and return time "10/04/2026 16:00" for the student with login "Vitoria"
    Then the system does not register any reservation
    And the system returns the error "The equipment 'Projector' is under maintenance and cannot be reserved"
    And no reservation is associated with the student with login "Vitoria"

  Scenario: Equipment pickup confirmation
    Given the student has a pending reservation for equipment type "Desktop Computer"
    When the student confirms the equipment pickup
    Then the reservation status becomes "In Use"
