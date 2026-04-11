Feature: Contact page validation
  As a user of the web application
  I want to be able to press "Contact" button
  So that I can slide down right to the Contact page

  @smoke @ui @demo
  Scenario: User opens page and navigates to contact form
    When I open the Profile page
    Then I should see the Okoliohlo profile homepage
    When I click the Contact button
    Then I should see the Contact form
