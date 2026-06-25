"""Example preference profile. Replace with your real ICP + current work."""
from __future__ import annotations

from linkedin_finder.models import Preferences, ICPQuery


def sample_preferences() -> Preferences:
    return Preferences(
        me="a platform engineer building real-time data infrastructure on Kafka",
        current_work=(
            "Standing up a multi-region Kafka cluster on AWS with Terraform, "
            "stream processing, schema governance, and data reliability."
        ),
        connection_rationale=(
            "I like trading notes with people running streaming data platforms at scale."
        ),
        tone="warm, concise, peer-to-peer, not salesy",
        exclude_companies=["My Current Employer Inc"],
        segments=[
            ICPQuery(
                label="streaming-data-leaders",
                titles=["Head of Data Platform", "Principal Data Engineer", "Staff Engineer"],
                industries=["Software", "Financial Services"],
                locations=["United States"],
                keywords=["kafka", "streaming", "data platform", "flink"],
                seniority=["senior", "principal", "staff", "director"],
                quota=20,
            ),
            ICPQuery(
                label="platform-peers",
                titles=["Platform Engineer", "SRE", "Infrastructure Engineer"],
                industries=["Software"],
                locations=["United States"],
                keywords=["terraform", "aws", "kubernetes", "reliability"],
                seniority=["senior", "staff"],
                quota=20,
            ),
            ICPQuery(
                label="thought-leaders",
                titles=["Developer Advocate", "Founder", "CTO"],
                industries=["Software"],
                locations=["United States"],
                keywords=["kafka", "event streaming", "data"],
                seniority=["director", "vp", "c-level"],
                quota=10,
            ),
        ],
    )
