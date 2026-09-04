# CargoFlow Sentinel — Build Day Runbook
Architect Track, Microsoft Agent-a-Thon, September 17, 2026 (12:30–3:30 PM CET, 3hr window)

## Before you arrive (do this the night before / morning of)
- [ ] Azure subscription confirmed with Contributor + Foundry User roles
- [ ] `.env` file created with `PROJECT_CONNECTION_STRING` and `MODEL_DEPLOYMENT_NAME`
- [ ] Codespace / local devcontainer opened once, dependencies installed, so pip install isn't eating build time
- [ ] `data/shipments.json` and `data/purchase_orders.json` already in place (done — see /data)
- [ ] System prompts drafted (done — see /agents/agents.py)
- [ ] Confirmed with organizers whether custom scenarios are judged equally to the three official ones

## Timeline (3 hour window)

| Time | Block | What you do |
|---|---|---|
| 0:00–0:15 | Setup | `az login`, verify `.env`, deploy model, run `client.agents.list()` sanity check |
| 0:15–0:45 | Build Agents | Run `agents/agents.py`, test each agent solo in the Foundry Playground |
| 0:45–1:05 | Monitor | Enable GenAI tracing via App Insights, run one scan, confirm trace spans appear |
| 1:05–1:30 | Evaluate | Run `eval/run_eval.py`, save `eval_results.json`, screenshot the portal eval view |
| 1:30–1:55 | Workflow | Run `workflow/workflow.py` end-to-end, rebuild the same flow visually in the Foundry portal |
| 1:55–2:20 | Polish | Fix anything broken, re-run full workflow once clean, confirm demo shipment IDs (below) work live |
| 2:20–2:45 | Package | Finalize talk track (see PRESENTATION.md), prep screen layout for demo |
| 2:45–3:00 | Buffer | Slack for anything that ran long. Do NOT use this time to add new features. |

## Demo shipment IDs to use live (pre-verified to hit each path)
- **SHP-1003** — CRITICAL, both delay AND cold-chain finding, triggers ERP reconciliation (production_dependency=true) — your headline example
- **SHP-1002** — WARNING only, shows the system doesn't over-escalate
- **SHP-1004** — OK, shows a clean pass (don't dwell on this one, just prove it exists)

## If something breaks under time pressure
Priority order to preserve, cut from the bottom if you're short on time:
1. Agent 1 + Agent 2 working end-to-end (this is your floor — never sacrifice this)
2. Conditional branch to Agent 3 (your key differentiator — fight to keep this)
3. Portal visual workflow rebuild (nice-to-have, code version is enough if cut)
4. Full eval suite (having even 1-2 eval results beats none — don't skip entirely, just trim case count)
