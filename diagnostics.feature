Feature: Diagnostics system and clients

  # @author chunchen@redhat.com
  # @case_id 501021
  @admin
  @destructive
  Scenario: Diagnose docker registry and router entities
    Given default docker-registry replica count is restored after scenario
    And default router replica count is restored after scenario
    Given I have a project
    When I run the :oadm_diagnostics client command with:
      | images | openshift3/ose-${component}:${version} |
      | latest-images | false |
    Then the output should not match "Errors seen:\s+[1-9]\d*"
    When I run the :scale admin command with:
      | resource | deploymentconfigs |
      | name | docker-registry |
      | replicas | 0 |
      | n | default|
    Then the step should succeed
    When I run the :scale admin command with:
      | resource | deploymentconfigs |
      | name | router |
      | replicas | 0 |
      | n | default|
    Then the step should succeed
    When I run the :oadm_diagnostics admin command with:
      | images | openshift3/ose-${component}:${version} |
      | latest-images | false |
    Then the output should match:
      | the registry will fail |
      | Apps will not be externally accessible |
      | Errors seen:\s+[1-9]\d* |

  # @author chunchen@redhat.com
  # @case_id 501020
  Scenario: Diagnose openshift client
    Given I have a project
    When I run the :oadm_diagnostics client command with:
      | images | openshift3/ose-${component}:${version} |
      | latest-images | false |
      | loglevel | 5 |
      | diaglevel | 0 |
    Then the output should match:
      | debug: |
      | I\d+\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+ |
    And the output should not match "Errors seen:\s+[1-9]\d*"
    When I run the :oadm_diagnostics client command with:
      | images | openshift3/ose-${component}:${version} |
      | latest-images | false |
      | config | /path/to/non-existed-file |
    Then the output should match:
      | not find config file |
      | Errors seen:\s+[1-9]\d* |

  # @author xiazhao@redhat.com
  # @case_id 526580
  @admin
  @destructive
  Scenario: Diagnostics container for docker registry and router as ordinary user
    Given I have a project
    # Diagnose when diag container is forbidden
    When I run the :oadm_diagnostics client command with:
      | diagnostics_name | DiagnosticPod |
      | prevent-modification | true |
    Then the output should match:
      | [sS]kipping diagnostic:\\s+DiagnosticPod |
      | .*API change.*prevented.* |
      | no errors or warnings seen |
    And the output should not contain:
      | Running diagnostic:\\s+DiagnosticPod |
    # Diagnose when latest-images is set to true
    When I run the :oadm_diagnostics client command with:
      | diagnostics_name | DiagnosticPod |
      | images | openshift3/ose-${component}:${version} |
      | latest-images | true |
    Then the output should match:
      | [oO]utput from.*diagnostic pod|
      | [rR]unning diagnostic:\\s+DiagnosticPod |
      | [sS]ervice account credentials authenticate.*expected |
      | [sS]ervice account token successfully authenticated.* |
      | [sS]ervice account token.*authenticated.*integrated.* |
      | DNS.*expected |
      | .*no errors.*|
    And the output should not match "Errors seen:\s+[1-9]\d*"
    Given default docker-registry replica count is restored after scenario
    And default router replica count is restored after scenario
    # Scale down router & registry pods' replica to zero
    When I run the :scale admin command with:
      | resource | deploymentconfigs |
      | name | docker-registry |
      | replicas | 0 |
      | n | default|
    Then the step should succeed
    When I run the :scale admin command with:
      | resource | deploymentconfigs |
      | name | router |
      | replicas | 0 |
      | n | default|
    Then the step should succeed
    # Diagnose when latest-images is set to false
    When I run the :oadm_diagnostics client command with:
      | diagnostics_name | DiagnosticPod |
      | images | openshift3/ose-${component}:${version} |
      | latest-images | false |
    Then the output should match:
      | [rR]unning diagnostic:\\s+DiagnosticPod |
      | [sS]ervice account credentials.*expected |
      | .*integrated registry timed out |
      | DNS.*expected |
      | Errors seen:\\s+\\d{1}|
