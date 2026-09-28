# Design notes

## Decision record

### Decision: SSM instead of SSH/WinRM

SSM removes the need to distribute private keys/passwords and eliminates inbound management ports. Ansible's `amazon.aws.aws_ssm` connection plugin executes through Systems Manager.

### Decision: CloudWatch Agent for continuous collection

A monitoring agent is more appropriate than a high-frequency Ansible job. The agent emits time-series data locally and CloudWatch provides aggregation, dashboards, alarms and cross-account observability.

### Decision: StackSets for account onboarding

A service-managed CloudFormation StackSet targeted at OUs can automatically deploy the execution role to new accounts. This removes the manual role-creation bottleneck.

### Decision: Dedicated monitoring account

Monitoring is separated from the AWS Organization management account. This reduces blast radius and lets operations teams receive observability access without broad management-account access.

## Alternatives considered

| Option | Pros | Cons | Decision |
|---|---|---|---|
| Ansible polling every minute | Uses only existing tool | Poor fit for time-series monitoring at scale | Not primary |
| SSH/WinRM + Ansible | Familiar | Inbound ports, credentials, network complexity | Rejected |
| SSM Run Command only | AWS-native and scalable | Better for commands/config than continuous telemetry | Used for management, not telemetry |
| CloudWatch Agent | Native metrics, alarms, dashboards, low controller load | Custom metrics have cost considerations | Primary telemetry path |
| Third-party monitoring | Rich features | Additional platform/cost | Outside current requirement |

## Operational assumptions

- EC2 instances run SSM Agent or can have it installed during image provisioning.
- EC2 instance profiles include `AmazonSSMManagedInstanceCore`.
- Production instances are tagged `DiskMonitoring=enabled`.
- Monitoring account has CloudWatch cross-account observability configured for monitored OUs.
- The Ansible controller has IAM permissions to list organization accounts and assume the target role.
