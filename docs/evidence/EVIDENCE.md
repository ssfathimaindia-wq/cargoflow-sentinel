# CargoFlow Sentinel — Evidence Index

Captured 2026-09-08, for the contest video and written description
("example interactions" / "key lessons learned" requirements).

## Live end-to-end run (primary proof)

The real, working proof of the system: `workflow/workflow.py` run against
the live Foundry project. All 3 agents invoked for real, 8 shipments
scanned, 4 flagged CRITICAL, conditional ERP reconciliation branch fired
correctly with real business-impact data (customer, order value,
production dependency). Full captured output: `workflow-run-output.txt`
(same session, after the SDK/tool-loop fixes were applied). Reproducible by
running `python agents/agents.py` then `python workflow/workflow.py`.

## Evaluation (LLM-as-judge)

`eval-results.json` — output of `eval/run_eval.py` against the live agents,
run after the SDK/tool-loop fixes and the conditional-tool-call prompt
update. 4 test cases, **average score 4.50 / 5**. 3 of 4 root-cause
diagnoses scored 5/5 (correctly identify both the customs delay and
cold-chain causes, with specific, actionable next steps). The ERP
reconciliation case scored 3/5 — the judge's own reasoning: correct on
business impact and urgency, but light on concrete escalation steps. This
is genuine, non-cherry-picked judge output, including its one lower score —
useful "we measured quality, and here's an honest weak spot" material for
the write-up, not just a clean sweep.

## Portal Foundry trace

`trace-exception-detection-agent.redacted.json` — a real GenAI trace span
from the Foundry portal's "Traces" view, captured while running the
`cargoflow-sentinel-workflow` portal Workflow. Shows: the exact system
prompt sent, the input message, the model's real output, model name
(gpt-5.4-nano), and Azure content-filter results (all "safe"). Good for a
brief on-screen trace glimpse per `Video_Storyboard.md` Scene 3.

The unredacted original (`trace-exception-detection-agent.raw.json`) is
gitignored — it contains real Azure subscription ID, resource group, and
project resource IDs.

## Portal Workflow (architecture visual, not a live demo)

Workflow name: `cargoflow-sentinel-workflow`, in the same Foundry project.
Graph: `Start -> exception-detection-agent -> root-cause-action-agent ->
If/else (CRITICAL check) -> erp-reconciliation-agent -> End`, with the Else
branch skipping straight to End. This visually demonstrates the same
conditional-branch architecture as the Python workflow.

Known limitation, not fixed: the portal's chat-triggered Preview cannot
fully execute past the If/else condition, because the agent's saved output
is a structured message Table (`gen_ai.output.messages[].parts[].content`),
not plain text, and the exact record/table accessor path for this Foundry
tenant's Power Fx dialect wasn't identified. The two tool-using agent nodes
(`exception-detection-agent`, `erp-reconciliation-agent`) DO run correctly
in Preview when given pre-fetched data directly in their Input message
(see the trace above) — only the conditional branch evaluation is
unresolved. This is a portal-specific gap; the real Python SDK path has no
such limitation and is the system's actual, complete proof of execution.

## Still to capture (do before recording the video)

- [ ] Portal screenshot: Agents list (all 3 CargoFlow Sentinel agents)
- [ ] Portal screenshot: `cargoflow-sentinel-workflow` graph view (full canvas)
- [ ] Terminal screenshot/recording: `python workflow/workflow.py` output
