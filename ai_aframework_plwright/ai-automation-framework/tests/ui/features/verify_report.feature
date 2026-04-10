Feature: CareLink report Verification
  As a user of the CareLink application
  I want to verify report functionality
  So that I can ensure the reports display correctly after authentication

  @smoke @ui @tc03
  Scenario: Verify reports after API login
    When I authenticate via API as "standard" user
    Then I navigate to the dashboard with authenticated session
    And I click on the reports tab
    Then I should see report elements
