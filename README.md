# AlgoJury Live v1

Privacy-first digital harm assessment and accountability tooling.

## What this version does

- Captures a structured incident without requiring an account.
- Runs deterministic safety/legal triage.
- Retrieves relevant passages from a versioned starter knowledge base.
- Separates allegations from legal conclusions.
- Highlights possible GBV relevance and escalation options.
- Can optionally call a local/open-weight LLM through an OpenAI-compatible endpoint.
- Includes security headers and a Render deployment configuration.
- Includes automated tests.

## Important boundary

AlgoJury is not a lawyer, court, police service, or adjudicator. It does not determine guilt or whether an offence has legally occurred. It provides structured issue spotting, evidence guidance, source passages, and next-step options.

The included legal/policy corpus is a curated starter set, not an exhaustive legal database. Before public production use, each source and update should be reviewed by an appropriately qualified South African legal/policy expert.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Optional local LLM

Set:
- `ALGOJURY_LLM_URL` to your local OpenAI-compatible chat endpoint
- `ALGOJURY_LLM_MODEL` to the local model name

The deterministic assessment remains the fallback if the LLM is unavailable.

## Render

This repo contains `render.yaml`. Create a Render Web Service from the repository and use the Blueprint/deploy configuration. The free Render tier is suitable for testing, not for a production privacy-sensitive deployment.

## Project structure

- `app/` API, assessment logic and retrieval
- `knowledge/chunks.json` retrievable legal/policy passages
- `corpus/sources.json` source/version manifest
- `frontend/` browser UI
- `tests/` automated tests
- `render.yaml` deployment configuration

## Safety

If someone is in immediate danger, contact emergency services. In South Africa, SAPS emergency is 10111. The GBV Command Centre is available 24/7 at 0800 428 428 or *120*7867#.
