Feature: CareLink Dashboard Verification
  As a user of the CareLink application
  I want to verify dashboard functionality
  So that I can ensure the dashboard displays correctly after authentication

  @smoke @ui @tc02
  Scenario: Verify dashboard after API login
    When I authenticate via API as "standard" user
    Then I navigate to the dashboard with authenticated session
    Then I should see dashboard elements
