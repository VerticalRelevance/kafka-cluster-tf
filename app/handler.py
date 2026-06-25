"""AWS Lambda entrypoint. Triggered daily by EventBridge Scheduler.

Loads the user's Preferences (from DynamoDB/SSM in real deployments), runs the
pipeline, and returns a summary. Notification (SES email / Slack) would be wired
as a downstream Step Functions task or appended here.
"""
from __future__ import annotations

import datetime

from linkedin_finder.config import load_config
from linkedin_finder.pipeline import run
from sample_preferences import sample_preferences


def lambda_handler(event, context):
    cfg = load_config()
    # In production, load Preferences from DynamoDB/SSM keyed by user id in `event`.
    prefs = sample_preferences()
    date = event.get("date") if isinstance(event, dict) and event.get("date") else \
        datetime.date.today().isoformat()
    batch = run(prefs, date, cfg)
    return {
        "date": batch["date"],
        "selected": batch["selected"],
        "considered": batch["considered"],
        "source": batch["source"],
    }
