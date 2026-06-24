# LinkedIn Daily Connection Finder — Solution Plan

> Goal: every day, surface **50 people worth connecting with**, ranked by *my preferences*
> and *what I'm currently working on*, each with a **custom drafted message** ready to send.

---

## 0. Read this first — compliance shapes everything

LinkedIn's User Agreement prohibits scraping and unauthorized automated access, and
LinkedIn aggressively detects headless browsers / automation. A bot that logs in as you,
crawls profiles, and auto-fires 50 invites/day will, in practice:

- get your account **restricted or permanently banned**,
- get the source IPs blocked,
- expose you to ToS / CFAA-adjacent legal risk.

LinkedIn also **rate-limits invitations** (~100–200/week, weekly cap enforced) and weights
acceptance rate, so volume-spam is self-defeating anyway.

**Design principle adopted here:** *machine proposes, human disposes.*
The system does all the heavy lifting — discovery, ranking, message drafting — and presents
a daily review queue. You click to send (or one-click approve) from a real LinkedIn session.
No credential-stuffing, no headless auto-send. This keeps the account safe and the output
high-quality.

Three sourcing tiers, in order of preference:

| Tier | Source | Compliance | Use |
|------|--------|-----------|-----|
| **A (preferred)** | LinkedIn official APIs (Marketing/Sales Navigator/Talent partner APIs) | Fully compliant | If you have/obtain API access |
| **B (default)** | Public web + licensed data providers (People Data Labs, Apollo, Proxycurl, Clearbit) | Compliant via vendor ToS | Main discovery engine |
| **C (assist only)** | Your own LinkedIn session, semi-automated **suggestions** you manually action | Gray; keep human-in-loop, low volume | Final send step only |

The architecture below defaults to **Tier B for discovery + Tier C human send**.

---

## 1. High-level architecture

```
                          ┌─────────────────────────────────────────┐
                          │            Daily Orchestration           │
                          │   (EventBridge cron → Step Functions)    │
                          └───────────────────┬─────────────────────┘
                                              │
        ┌──────────────┬──────────────────────┼───────────────────┬─────────────────┐
        ▼              ▼                       ▼                   ▼                 ▼
 ┌────────────┐ ┌─────────────┐        ┌─────────────┐    ┌──────────────┐  ┌──────────────┐
 │ Preference │ │  Discovery  │        │   Scoring   │    │   Message    │  │   Review     │
 │  Profile   │ │  (sourcing) │  ───▶  │  & Ranking  │──▶ │  Generation  │─▶│   Queue      │
 │  Service   │ │  connectors │        │   engine    │    │ (LLM/Claude) │  │ (web app +   │
 └────────────┘ └─────────────┘        └─────────────┘    └──────────────┘  │  notify)     │
        │              │                       │                  │          └──────┬───────┘
        ▼              ▼                       ▼                  ▼                 ▼
    DynamoDB      Vendor APIs            Vector store        Anthropic API     You click
   (prefs +     (PDL/Apollo/             (embeddings,        (Claude)          "send" in
    work ctx)    Proxycurl)              dedupe, history)                      LinkedIn
```

Everything is event-driven and stateless between runs; state lives in DynamoDB + an object
store. One daily run produces one reviewable batch of 50.

---

## 2. Hosting — how to run it

**Recommendation: serverless on AWS** (matches this repo's existing Terraform/AWS posture;
you already have remote state + a CodePipeline build setup here).

| Component | Service | Why |
|-----------|---------|-----|
| Scheduler | **EventBridge Scheduler** (cron, e.g. `0 13 * * ? *`) | Daily trigger, no server |
| Orchestration | **Step Functions** | Sequences discovery → score → message → queue; retries/backoff per stage |
| Compute | **Lambda** (Python) per stage; **Fargate** task if a stage needs >15 min or a browser | Pay-per-run, scales to zero |
| State / dedupe | **DynamoDB** (prefs, seen-people, send history, daily batch) | Serverless, fast key lookups |
| Vector search | **OpenSearch Serverless** *or* **pgvector on Aurora Serverless v2** | Semantic match of people↔work context, dedupe |
| Secrets | **Secrets Manager** | Vendor API keys, Anthropic key, LinkedIn OAuth tokens |
| Review UI | **Amplify / S3+CloudFront static SPA** + **API Gateway + Lambda** backend | The human-in-loop dashboard |
| Notifications | **SES** (daily email digest) and/or **SNS**→Slack | "Your 50 are ready" |
| IaC | **Terraform** (this repo) | Consistent with existing modules |

Cost is low — one batch/day of 50 ≈ a few thousand vendor lookups/month + ~50 LLM
generations/day. Expect tens of dollars/month plus vendor data subscription.

> Lighter alternative if you don't want AWS: a single small VM (or Fly.io / Railway
> container) running a cron job + SQLite/Postgres + a tiny Flask/FastAPI review page.
> Same logic, less ops. Start here for a v0, graduate to serverless for reliability.

---

## 3. How to "call LinkedIn" / source candidates

### 3.1 Tier A — Official LinkedIn APIs (if accessible)
- **Marketing Developer Platform / Sales Navigator / Talent Solutions** partner APIs.
- Requires LinkedIn app + OAuth 2.0 (3-legged) + program approval. Not open to everyone.
- Use for: enrichment, your own network graph, posting. *Not* a general people-search firehose.
- Store OAuth tokens in Secrets Manager; refresh on schedule.

### 3.2 Tier B — Licensed data providers (the real discovery engine)
These vendors provide people/company search + enrichment **compliantly under their own ToS**,
so you never touch LinkedIn's site directly:

- **People Data Labs** — person/company search API, good for ICP filtering at scale.
- **Apollo.io** — search by title/industry/keywords/seniority + contact data.
- **Proxycurl** — profile + people-search endpoints (LinkedIn-shaped data, licensed).
- **Clearbit / Crunchbase** — company-side enrichment & signals.

Build a thin **connector interface** so providers are swappable:

```python
class PeopleSource(Protocol):
    def search(self, query: ICPQuery, cursor: str | None) -> SearchPage: ...
    def enrich(self, person_id: str) -> PersonProfile: ...
```

Query inputs derive from your preferences + current work (titles, industries, geographies,
skills, keywords, company stage, seniority).

### 3.3 Tier C — Your own session (send step only)
- Final "send connection request + note" is done by **you**, from the dashboard, in a real
  LinkedIn tab. Optionally a browser extension pre-fills the personalized note (you still click).
- Keep daily volume sane (≤ ~20–25 sends/day, well under LinkedIn's weekly cap) to protect
  acceptance rate and the account.

### 3.4 Signals that make targeting smart
Pull "reasons to reach out now" from compliant public/vendor signals: recent job changes,
funding rounds, conference speakers, mutual connections, content they posted, shared groups,
alumni overlap. These directly feed both ranking and the message.

---

## 4. How to allocate / select the 50 individuals

A four-stage funnel, run daily:

**Stage 1 — Candidate generation (pull ~500–1,000).**
Translate your preference profile into N provider queries (one per ICP segment), page through
results.

**Stage 2 — Filtering & dedupe.**
- Drop anyone already connected, already invited, already in `seen-people`, or who declined.
- Hard filters: geography, seniority floor, must-have keywords, exclude current employer/
  competitors if desired.
- Dedupe across providers by (name + company + normalized title) and by embedding similarity.

**Stage 3 — Scoring (rank the survivors).**
Composite score per candidate:

```
score = w1 * fit_to_preferences        # cosine(sim) of profile ↔ your ICP/preference vector
      + w2 * relevance_to_current_work # cosine(sim) of profile ↔ your active projects/notes
      + w3 * timeliness_signal         # recent job change / funding / posted / event
      + w4 * connection_path_strength  # mutual connections, alumni, shared groups
      + w5 * reachability / seniority_match
      - w6 * over_saturation_penalty   # too many from same company this week
```

- Build the **preference vector** and **current-work vector** with embeddings (Claude/an
  embeddings model) over: a preferences doc you maintain + a live feed of what you're working
  on (Jira/Notion/GitHub/README/calendar — your choice of input).
- Weights `w1..w6` are tunable and **learned over time** from your accept/reject/sent feedback.

**Stage 4 — Diversification & pick 50.**
Don't just take top-50 by raw score — apply quotas so the batch is balanced:
- cap per-company, per-title, per-segment,
- reserve slots across your ICP segments (e.g. 15 prospects / 15 peers / 10 hiring / 10 thought-leaders),
- use **Maximal Marginal Relevance (MMR)** to trade off score vs. diversity.

Output: a ranked, deduped, diversified list of exactly 50, each with the *why* (top signals)
attached for the message step.

---

## 5. How to create the custom message for each person

Use **Claude (Anthropic API)** with structured inputs and strict guardrails.

**Per-person prompt inputs:**
- their public/vendor profile summary (role, company, recent activity, the matched signal),
- **your** identity + what you're working on + why you'd want to connect,
- the *specific reason this person scored high* (the signal — e.g. "just joined X as Head of Data"),
- tone/voice settings from your preferences,
- the LinkedIn note constraint: **≤ 300 characters** (connection-request note limit).

**Generation rules baked into the system prompt:**
- Reference one concrete, true detail about them (the matched signal) — no generic flattery.
- State a clear, honest reason for connecting tied to your current work.
- One soft, low-pressure ask. No sales pitch in a first touch.
- Never fabricate shared history or mutual connections; only use provided facts.
- Output two variants (short ≤300 char note + a longer follow-up DM for after they accept).

**Pattern:** batch-call Claude for all 50, with a JSON schema response
(`{person_id, note, followup, rationale}`), then store drafts in the daily batch record.
Add a lightweight quality gate (length check, banned-phrase filter, profanity/PII check)
before anything reaches the queue.

**Example skeleton:**
```
You are drafting a LinkedIn connection note from {me} to {them}.
Facts about them (do not invent beyond these): {profile_summary}, {trigger_signal}.
What I'm working on: {current_work}. Why connect: {connection_rationale}.
Write a ≤300-character note: reference {trigger_signal} specifically, give one honest reason
to connect tied to my work, one low-pressure ask, warm but not salesy. Then a 2-3 sentence
follow-up DM for after they accept.
```

---

## 6. The daily human-in-the-loop flow

1. **13:00 UTC** — EventBridge fires Step Functions.
2. Discovery → filter → score → diversify → 50 picked.
3. Claude drafts note + follow-up for each.
4. Batch saved to DynamoDB; **SES email + Slack ping**: "Your 50 are ready."
5. You open the **review dashboard**: each card shows person, why-they-matched, editable note.
   - **Approve** (copies note + opens their LinkedIn profile in a new tab to send), **Edit**, or **Skip**.
6. Your actions write back to `feedback` → tunes weights and trains the next day's batch.
7. Anyone skipped/declined goes to `seen-people` so they never resurface.

This is the safe, high-acceptance version of "auto-connect 50/day."

---

## 7. Data model (DynamoDB sketch)

- `Preferences` (PK=`user`) — ICP segments, weights, tone, exclusions, work-context sources.
- `People` (PK=`person_id`) — canonical profile, provenance, embedding ref, status
  (`new|queued|sent|connected|declined|skipped`), last_seen.
- `DailyBatch` (PK=`date`) — the 50 picks + scores + drafted messages.
- `Feedback` (PK=`person_id`, SK=`ts`) — your approve/edit/skip, used for weight learning.
- `Signals` (PK=`person_id`, SK=`signal_type`) — job change, funding, post, event, etc.

---

## 8. Build phases

- **Phase 0 (v0, ~days):** one Lambda/cron + one provider (e.g. Apollo or PDL) + Claude
  drafting + a daily email of 50 with notes. SQLite/DynamoDB. Prove the value end-to-end.
- **Phase 1:** add scoring with embeddings + preference/work vectors; dedupe + seen-people.
- **Phase 2:** review dashboard with approve/edit/skip + feedback write-back.
- **Phase 3:** diversification quotas + learned weights; multi-provider connectors.
- **Phase 4:** Tier-A official API integration (if approved); signal enrichment; analytics
  (acceptance rate, best segments/messages).

---

## 9. Key risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Account ban from automated send | Human-in-loop send; volume caps; never headless-login |
| ToS / legal exposure | Source via licensed vendors (Tier B), official APIs (Tier A) |
| Low acceptance rate | Diversification + genuine personalized signals + quality gate |
| Data staleness / dupes | seen-people store, embedding dedupe, signal recency weighting |
| Vendor lock-in | `PeopleSource` connector abstraction, swappable providers |
| LLM hallucinated personalization | Facts-only prompt + post-gen verification gate |
| Cost creep | Cap candidate pulls/day; cache enrichment; batch LLM calls |

---

## 10. Tech stack summary

- **IaC:** Terraform (this repo) — EventBridge, Step Functions, Lambda, DynamoDB, Secrets Manager, SES, OpenSearch/Aurora.
- **Language:** Python (Lambdas, connectors, scoring).
- **LLM:** Anthropic Claude (`claude-opus-4-8` for drafting/judging; an embeddings model for vectors).
- **Data providers:** People Data Labs / Apollo / Proxycurl (pick 1 to start).
- **Frontend:** static SPA (React/Amplify) + API Gateway + Lambda.
- **Notify:** SES + SNS/Slack.

---

### Bottom line
You *can* have "50 great people to connect with, personalized message each, every morning."
Build it as **automated discovery + ranking + AI drafting**, with a **human one-click send**
from a real session and **licensed data sources** — not a LinkedIn scraper-bot. That gets you
the daily outcome you want without torching your account or crossing ToS lines.
