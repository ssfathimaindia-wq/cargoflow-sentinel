# CargoFlow Sentinel
Microsoft Agent-a-Thon — Level 3: Architect track submission.

A three-agent logistics monitoring system on Microsoft Foundry: detects
shipment exceptions, diagnoses root cause, and conditionally escalates
CRITICAL cases to an ERP reconciliation agent for business-impact assessment.

Built on the same Foundry concepts as the official `factory/` lab in
[microsoft/FrontierWeekHack](https://github.com/microsoft/FrontierWeekHack),
with a custom scenario, dataset, and an added third agent + conditional
branch beyond the lab's baseline two-agent pipeline.

## Structure
```
data/            Mock shipment + purchase order datasets
agents/          Tool functions and agent definitions (3 agents)
workflow/        Orchestration with conditional ERP escalation branch
eval/            LLM-as-judge evaluation dataset + runner
docs/            RUNBOOK.md (day-of timeline) and PRESENTATION.md (talk track)
```

## Setup
1. `pip install azure-ai-projects azure-identity python-dotenv`
2. Copy `.env.example` to `.env`, fill in your Foundry project connection
   string and model deployment name
3. `az login`
4. `python agents/agents.py` — deploys all three agents
5. `python workflow/workflow.py` — runs the full pipeline end-to-end
6. `python eval/run_eval.py` — runs the evaluation suite

## Read first
- `docs/RUNBOOK.md` — exact build-day timeline and fallback priorities
- `docs/PRESENTATION.md` — full talk track and anticipated Q&A
