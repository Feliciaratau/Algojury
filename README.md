# AlgoJury Live — Offline-First Digital Harm Assessment

This package turns the AlgoJury concept into a runnable local-first application.

## What it does
- Captures a digital-harm incident locally in the browser.
- Runs a deterministic safety/legal triage layer for common South African digital-abuse patterns.
- Optionally calls a **local LLM** through `llama.cpp` (OpenAI-compatible HTTP API) when available.
- Keeps user incident text local by default.
- Produces a structured assessment with source identifiers, confidence, safety actions and a clear non-legal-advice boundary.
- Includes a versioned legal/policy corpus manifest and an evaluation suite.

## Important design decision
AlgoJury does **not** fine-tune an LLM on legislation. Laws change. Instead, legislation and policy are maintained as a versioned retrieval corpus and the model is instructed to ground claims in retrieved passages. This package ships the corpus manifest and ingestion interfaces; official source documents should be downloaded and reviewed by a qualified legal/domain reviewer before production use.

## Run locally — no AI provider required
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000

The app works in **deterministic offline mode** without a model. This is intentional: the safety/legal triage must not disappear if the LLM is unavailable.

## Run with a local LLM
Install `llama.cpp`, then start its OpenAI-compatible server with a local GGUF model. The official project documents `llama serve` and local CPU/Metal/CUDA backends. See the official project documentation.

Then set:
```bash
export ALGOJURY_LLM_URL=http://127.0.0.1:8080/v1/chat/completions
export ALGOJURY_LLM_MODEL=local-model
```
Restart the API. AlgoJury will use the local model only; it will not call a cloud model.

## Production architecture
Browser/PWA → FastAPI → deterministic safety layer → local retrieval corpus → local LLM → structured assessment.

For a real public deployment, add:
- HTTPS and secure headers
- encrypted-at-rest case storage
- explicit consent and retention controls
- authenticated reviewer/admin area
- immutable audit log
- legal/domain expert validation of the corpus
- model/evaluation monitoring
- crisis escalation UX
- independent security and privacy review

## Corpus
`corpus/sources.json` contains authoritative starting sources and update metadata. The current manifest includes UNESCO AI ethics/digital-platform guidance and South African legislation including Cybercrimes, POPIA, Protection from Harassment and Domestic Violence. The Domestic Violence source must be maintained against amendments and regulations.

## Evaluation
Run:
```bash
pytest -q
```
The tests verify the safety classifier, source mapping and LLM fallback behavior. They do not constitute legal validation.

## Disclaimer
AlgoJury provides information, evidence structuring and redress navigation. It is not a court, law-enforcement system or substitute for a lawyer or qualified support professional. Never present its output as a finding of guilt or definitive legal advice.
