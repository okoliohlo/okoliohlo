Feature: CareLink Login
  As a user of the CareLink application
  I want to be able to log in
  So that I can access my account

  @smoke @ui @tc01
  Scenario: User opens page and navigates to login
    When I open the CareLink page
    Then I should see the CareLink homepage
    When I click the sign in button
    Then I should see the login form
    When I login as "standard" user
    Then I should be logged in successfully