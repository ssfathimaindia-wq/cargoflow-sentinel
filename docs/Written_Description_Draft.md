# CargoFlow Sentinel — Written Description (Draft)

For the contest's written-description requirement: problem addressed, impact,
and how it was built using Foundry. Draft — edit freely, this is a starting
point in your voice, not a final copy to submit as-is.

## The problem, simply

An ERP knows the paperwork — what was ordered, who it's for, what it's
worth. A freight tracking system knows where the truck actually is. Those
are two different systems, and at most companies they don't talk to each
other in real time. So today, a coordinator manually checks a tracking
portal, then separately has to remember or look up whether that particular
shipment actually matters — which customer, what value, does it feed a
production line. Nobody does that cross-check automatically. The result is
reactive: problems surface when someone happens to check, or when a
customer calls first — and by then, the cheap moment to act on it has
usually already passed.

## The solution

CargoFlow Sentinel is a three-agent system on Microsoft Foundry. An
Exception Detection Agent checks every shipment against SLA and cold-chain
thresholds. A Root-Cause & Action Agent diagnoses *why* and recommends one
concrete next step. The third agent — ERP Reconciliation — only runs when
severity is genuinely CRITICAL, and automatically looks up the linked
purchase order to report who's affected, what it's worth, and whether it
blocks a production line. That conditional branch is the core design
choice: not every exception needs an ERP hop, only the ones that carry real
business risk.

## Where the value actually comes from

Not from the AI reasoning — from latency. The same refrigeration fault
costs almost nothing caught at 30 minutes and can be a write-off caught at
8 hours. Earlier, consistent detection is the entire value proposition.
Concretely, that shows up as:

- **Avoided demurrage** — a customs hold caught early is a phone call, not
  a fee.
- **Avoided spoilage** — a cold-chain breach flagged while the load is
  still moving is a redirected shipment, not a written-off one.
- **Protected production schedules** — when a shipment feeds a factory, the
  ERP agent surfaces that dependency automatically, before the line stalls.
- **Consistent triage** — every shipment gets the same check every cycle;
  it doesn't get skipped because a coordinator was busy.

No fabricated savings figure here deliberately — this is a working
prototype on representative data, not a year of measured production
outcomes. For scale, in the system's own test scenario a single undetected
CRITICAL shipment was tied to a €41,200 order with a live production
dependency; that's the shape of what gets caught, not a promised number.

## Who this fits

The strongest fit is a business with three things at once: shipment volume
past what one person can comfortably watch, cargo where delay has a real
cost (cold-chain, JIT production components, customs-exposed freight), and
an ERP that already tracks which purchase order belongs to which customer
and, ideally, which production order. Microsoft Dynamics 365 Finance &
Operations is the natural fit — the ERP Reconciliation Agent's data model
(`PurchTable`/`PurchLine`, `CustAccount`, `ProdTable`) is built directly
against it — though the pattern generalizes to any ERP with that same
purchase-order-to-customer-to-production structure.

Concretely: cold-chain food and pharma/biologics distributors, contract
manufacturers with imported JIT components, freight forwarders and 3PLs
looking to layer business-impact awareness on top of tracking data they
already have, and — most directly for me — D365 F&O implementation
partners' existing client bases, since this is an extension pitch to
accounts that already have the ERP structure this depends on, not a
cold-start sale.

## How to know it fits a given business — the qualifying questions

1. More in-transit shipments than one person can watch comfortably?
2. Does a delay ever cost real money — spoilage, penalty, stalled
   production, demurrage?
3. Is there a defined owner who gets alerted when something's critical?
4. Is the PO-to-customer-to-production link already tracked anywhere, even
   informally?
5. Does the ERP expose that data via an API?
6. Does the tracking/TMS/3PL system expose status via API, not just a
   portal a human reads?
7. Already on Azure, or open to it?

Mostly yes across the board — strong, close-to-as-is fit. A "no" on 5 or 6
specifically isn't disqualifying, but it means the first phase of work is a
data-access integration project before the agents add value — worth saying
plainly rather than implying it's plug-and-play.

## How it was built with Foundry

Three agents deployed to a live Microsoft Foundry project, built on
`azure-ai-projects`. Two independent orchestration paths chain them with
the same conditional logic and both run end-to-end against the live
deployment: a Python service (the production-grade path) and a visual
workflow built in Foundry's own drag-and-drop builder (useful for this
proof of concept, though Microsoft is retiring that specific builder
December 1, 2026 — the Python path is the durable one). Every diagnosis is
scored by a separate judging model against hand-written test cases, not
just eyeballed once: 4.5/5 average, including one honestly lower-scoring
case kept as-is rather than re-run until it looked better.

## Scope, stated plainly

Built and proven: live deployed agents, both orchestration paths working
end-to-end, a real evaluation harness, real GenAI trace telemetry. Not yet
built: live data sources (currently structured mock data shaped like the
real thing, not a live carrier-tracking feed or a live D365FO connection),
and a standing deployment (it runs on demand today; production needs a
schedule or event trigger, not a terminal command). That gap is almost
entirely data-and-trigger integration work — the agent reasoning itself is
already proven.
