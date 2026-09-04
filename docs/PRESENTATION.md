# CargoFlow Sentinel — Presentation Script
Target: 5-7 minutes total (confirm exact slot length with organizers).

## 1. Problem (30 seconds)
"Logistics teams monitor shipments manually against SLAs — delay thresholds,
cold-chain limits, customs timing. When something goes wrong, someone has to
notice it, figure out why, and then separately check whether it actually
matters to the business. That loop is slow and inconsistent."

## 2. Solution, one sentence (15 seconds)
"CargoFlow Sentinel is a three-agent system on Microsoft Foundry that detects
shipment exceptions, diagnoses the root cause, and — critically — only escalates
to a business-impact check when it's actually worth a human's attention."

## 3. Architecture (60 seconds — show the diagram, don't read code)
Walk through the pipeline verbally:
- Exception Detection Agent scans shipments against SLA thresholds (delay,
  temperature) — pure detection, no judgment calls
- Root-Cause & Action Agent diagnoses why and recommends a specific next step
- ERP Reconciliation Agent — **only fires on CRITICAL cases** — cross-references
  the shipment against purchase order data: customer, order value, whether a
  production line depends on it

Explicitly say: "That third agent and the conditional branch are the parts
that go beyond the base lab pattern — most pipelines here will be two agents,
straight-line. This one branches based on severity, and ties back to a real
business system, which is the pattern I use in my day job doing D365
ERP integration work."

## 4. Live demo (2-2.5 minutes)
Run `workflow/workflow.py` live, narrate as it streams:
1. "Scanning all shipments..." — point out CRITICAL vs WARNING counts appearing
2. "SHP-1003 is CRITICAL on two fronts — a customs delay AND a cold-chain
   breach. Watch the diagnosis..." — let the root-cause output print
3. "Because it's CRITICAL, it automatically escalates to ERP reconciliation —
   here's the business impact: Warsaw Manufacturing, EUR 58,900 order,
   production line dependency. That's the sentence a supply chain manager
   actually needs, not the raw sensor data."
4. Switch to the Foundry portal — show the trace view for that same run: "You
   can see all three agent spans in one trace, which is what makes this
   debuggable and auditable in production, not just a demo trick."

## 5. Evaluation (30 seconds)
Show `eval_results.json` or the portal eval view briefly:
"We didn't just build this and hope it works — we ran an LLM-as-judge eval
against known-good diagnoses. Average score X/5 across test cases." (fill in
your real number after running eval)

## 6. Close (20 seconds)
"This is a pattern that generalizes past logistics — anywhere you have
monitoring data on one side and a business system of record on the other,
this three-agent shape — detect, diagnose, reconcile — applies. Happy to
answer questions."

## Anticipated judge questions — have answers ready
- **"Why not just one agent that does everything?"** — Separation of concerns:
  each agent has a single, testable responsibility, which is also why the
  eval scores are meaningful per-stage rather than one opaque black box.
- **"Is the ERP data real?"** — Mocked for the demo, but structured the way a
  real D365FO OData/DMF query would return it — swapping the mock for a live
  call is a connector change, not an architecture change.
- **"How does this scale beyond 8 shipments?"** — The threshold-check tool is
  O(1) per shipment; the real scaling question is agent invocation cost/latency
  at volume, which is exactly what the tracing and eval instrumentation is
  there to monitor over time.
- **"What would you build next?"** — A fourth agent that learns threshold
  tuning from historical false-positive rates, or a scheduling loop that runs
  the scan continuously instead of on-demand.

## What to have visibly open during Q&A
- Terminal with `workflow.py` output still visible (scroll back if needed)
- Foundry portal trace view, on the SHP-1003 run
- `eval_results.json` open in an editor tab
