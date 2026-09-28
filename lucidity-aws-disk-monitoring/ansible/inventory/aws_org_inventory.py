#!/usr/bin/env python3
"""Dynamic Ansible inventory for an AWS Organization.

The controller identity lists member accounts, assumes a standardized role in
those accounts, discovers EC2 instances, and emits host variables required by
amazon.aws.aws_ssm.

Required environment variables:
  AWS_ROLE_NAME       target role name (default: DiskMonitoringExecutionRole)
  AWS_S3_BUCKET       S3 bucket used by the Ansible SSM connection plugin
  AWS_REGIONS         comma-separated Regions (default: AWS_REGION)
  DISK_MONITOR_TAG    tag key (default: DiskMonitoring)
  DISK_MONITOR_VALUE  tag value (default: enabled)
"""
import json
import os
import sys
from typing import Dict, List

import boto3

ROLE_NAME = os.getenv("AWS_ROLE_NAME", "DiskMonitoringExecutionRole")
S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
REGIONS = [r.strip() for r in os.getenv("AWS_REGIONS", os.getenv("AWS_REGION", "us-east-1")).split(",") if r.strip()]
TAG_KEY = os.getenv("DISK_MONITOR_TAG", "DiskMonitoring")
TAG_VALUE = os.getenv("DISK_MONITOR_VALUE", "enabled")


def assume(account_id: str):
    sts = boto3.client("sts")
    return sts.assume_role(
        RoleArn=f"arn:aws:iam::{account_id}:role/{ROLE_NAME}",
        RoleSessionName="ansible-disk-monitoring",
        DurationSeconds=3600,
    )["Credentials"]


def client(service: str, region: str, creds):
    return boto3.client(
        service,
        region_name=region,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )


def active_accounts() -> List[str]:
    org = boto3.client("organizations")
    ids = []
    paginator = org.get_paginator("list_accounts")
    for page in paginator.paginate():
        for account in page.get("Accounts", []):
            # AWS Organizations uses State for current account lifecycle state.
            if account.get("State") == "ACTIVE" or (not account.get("State") and account.get("Status") == "ACTIVE"):
                ids.append(account["Id"])
    return ids


def build_inventory() -> Dict:
    inventory = {"_meta": {"hostvars": {}}}
    for account_id in active_accounts():
        try:
            creds = assume(account_id)
        except Exception as exc:
            print(f"WARNING: unable to assume role in {account_id}: {exc}", file=sys.stderr)
            continue

        for region in REGIONS:
            ec2 = client("ec2", region, creds)
            paginator = ec2.get_paginator("describe_instances")
            filters = [
                {"Name": "instance-state-name", "Values": ["running"]},
                {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
            ]
            for page in paginator.paginate(Filters=filters):
                for reservation in page.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        iid = instance["InstanceId"]
                        host = f"{account_id}_{region}_{iid}"
                        tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                        image = instance.get("ImageId", "unknown")
                        inventory["_meta"]["hostvars"][host] = {
                            "ansible_connection": "amazon.aws.aws_ssm",
                            "ansible_aws_ssm_instance_id": iid,
                            "ansible_aws_ssm_region": region,
                            "ansible_aws_ssm_bucket_name": S3_BUCKET,
                            "ansible_aws_ssm_bucket_sse_mode": "aws:kms",
                            "ansible_aws_ssm_access_key": creds["AccessKeyId"],
                            "ansible_aws_ssm_secret_key": creds["SecretAccessKey"],
                            "ansible_aws_ssm_session_token": creds["SessionToken"],
                            "aws_account_id": account_id,
                            "aws_region": region,
                            "ec2_instance_id": iid,
                            "ec2_instance_type": instance.get("InstanceType", "unknown"),
                            "ec2_image_id": image,
                            "ec2_tags": tags,
                            "monitoring_enabled": True,
                        }
                        inventory.setdefault("all", {}).setdefault("hosts", []).append(host)
                        inventory.setdefault("accounts", {}).setdefault("children", []).append(account_id)
                        inventory.setdefault(account_id, {}).setdefault("hosts", []).append(host)
                        inventory.setdefault(f"region_{region.replace('-', '_')}", {}).setdefault("hosts", []).append(host)
        
    return inventory


if __name__ == "__main__":
    if "--host" in sys.argv or "--list" in sys.argv:
        print(json.dumps(build_inventory(), indent=2))
    else:
        print(json.dumps(build_inventory(), indent=2))
