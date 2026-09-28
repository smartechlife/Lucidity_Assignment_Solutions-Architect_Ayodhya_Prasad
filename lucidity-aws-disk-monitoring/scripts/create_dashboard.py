#!/usr/bin/env python3
"""Create/update a starter CloudWatch dashboard in the monitoring account."""
import json
import os
import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")
NAME = os.getenv("DASHBOARD_NAME", "Enterprise-Disk-Health")

widgets = [
    {
        "type": "text",
        "x": 0, "y": 0, "width": 24, "height": 2,
        "properties": {"markdown": "# Enterprise Disk Health\nThresholds: warning 80%, critical 90%, emergency 95%."}
    },
    {
        "type": "metric",
        "x": 0, "y": 2, "width": 24, "height": 8,
        "properties": {
            "view": "timeSeries",
            "region": REGION,
            "title": "Disk used percent",
            "stat": "Maximum",
            "period": 300,
            "metrics": [["Enterprise/Disk", "disk_used_percent", {"label": "Linux disk used %", "visible": True}], ["Enterprise/Disk", "disk_free_percent", {"label": "Windows disk free %", "visible": True}]],
        },
    },
]

cw = boto3.client("cloudwatch", region_name=REGION)
cw.put_dashboard(DashboardName=NAME, DashboardBody=json.dumps({"widgets": widgets}))
print(f"Dashboard created: {NAME} in {REGION}")
