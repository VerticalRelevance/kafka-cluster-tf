# LinkedIn Connection Finder — Phase 0 scaffold

A runnable skeleton of the daily pipeline:

```
discover (licensed provider) -> filter/dedupe -> score -> diversify (pick 50)
  -> draft message (Claude) -> save batch -> notify
```

Locked decisions: **human-in-the-loop send**, **licensed data provider**, **AWS serverless**.

## Layout
- `linkedin_finder/config.py`     — env-driven config
- `linkedin_finder/models.py`     — core dataclasses
- `linkedin_finder/sources/`      — swappable `PeopleSource` connectors (PDL/Apollo stubs)
- `linkedin_finder/scoring.py`    — composite score + diversified pick-50
- `linkedin_finder/messaging.py`  — Claude draft (note <=300 chars + follow-up)
- `linkedin_finder/store.py`      — DynamoDB / local-JSON persistence
- `linkedin_finder/pipeline.py`   — orchestrates one daily run
- `handler.py`                    — Lambda entrypoint
- `run_local.py`                  — run the whole thing locally with stub data

## Quick start (local, no AWS, no API keys)
```bash
cd app
pip install -r requirements.txt          # boto3 + anthropic (optional for dry run)
python run_local.py                       # uses StubSource + dry-run messages
```
Set `ANTHROPIC_API_KEY` to get real Claude-drafted notes. Set `PDL_API_KEY` /
`APOLLO_API_KEY` and `PEOPLE_SOURCE=pdl|apollo` to use a real provider.

## Infra
Terraform for the serverless stack is in `../infra-linkedin/` (EventBridge schedule,
Lambda, DynamoDB). It is intentionally minimal and separate from the Kafka stack.
