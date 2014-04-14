*** Settings ***

Variables  pyramid_robot/tests/robot/variables.py

Library  Selenium2Library  timeout=${SELENIUM_TIMEOUT}  implicit_wait=${SELENIUM_IMPLICIT_WAIT}

Suite Setup  Suite Setup
Suite Teardown  Suite Teardown

*** Test Cases ***

Scenario: Test Hello View
     When I go to  ${APP_URL}
     Then Page Should Contain  I am a max server

*** Keywords ***

Suite Setup
  Open browser  ${APP_URL}  browser=${BROWSER}  remote_url=${REMOTE_URL}  desired_capabilities=${DESIRED_CAPABILITIES}

Suite Teardown
  Close All Browsers

I go to
    [Arguments]  ${location}
    Go to  ${location}
