# Validation checklist

1. `ansible-inventory ... --graph` discovers all opted-in EC2 instances.
2. Inventory host variables contain account ID, Region, instance ID and temporary SSM credentials.
3. `collect_disk_once.yml` succeeds on one Linux and one Windows test VM.
4. CloudWatch Agent is running after `enroll_cloudwatch_agent.yml`.
5. `Enterprise/Disk` emits data every 60 seconds.
6. Dashboard can see source-account metrics from the monitoring account.
7. Warning/critical alarms fire after deliberately filling a test filesystem above the threshold.
8. Missing-agent test: stop the CloudWatch Agent and verify stale/missing-data alerting.
9. New-account test: add a sandbox account to the monitored OU and verify StackSet role auto-deployment.
10. New-instance test: launch an EC2 instance with SSM + `DiskMonitoring=enabled` and verify automatic discovery on the next Ansible run.
