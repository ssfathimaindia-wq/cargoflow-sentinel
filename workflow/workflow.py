"""
CargoFlow Sentinel - Production Workflow
Orchestrates all three agents. Unlike the Factory lab's linear two-agent
pipeline, this has a CONDITIONAL branch: the ERP Reconciliation Agent only
fires for CRITICAL exceptions. This is the architectural differentiator
worth calling out explicitly when presenting.
"""

import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents"))

from tools import scan_all_shipments, check_po_impact  # noqa: E402
from agents import (  # noqa: E402
    _get_client,
    invoke_agent,
    EXCEPTION_AGENT_NAME,
    ROOTCAUSE_AGENT_NAME,
    ERP_AGENT_NAME,
    deploy_agents,
)


def ensure_agents_deployed():
    print("=== Step 0: Ensuring agents deployed ===")
    deploy_agents()


def run_exception_scan() -> dict:
    """Step 1: Exception Detection Agent scans all shipments."""
    print("\n=== Step 1: Exception Scan ===")
    results = scan_all_shipments()
    print(f"  Checked {results['total_checked']} shipments")
    print(f"  CRITICAL: {len(results['critical'])}  WARNING: {len(results['warning'])}  OK: {results['ok_count']}")
    return results


def run_root_cause_diagnosis(client, flagged_shipments: list) -> list:
    """Step 2: Root-Cause & Action Agent diagnoses every WARNING/CRITICAL shipment."""
    print("\n=== Step 2: Root-Cause Diagnosis ===")
    diagnoses = []
    for shipment in flagged_shipments:
        print(f"  Diagnosing {shipment['shipment_id']}...")
        output_text = invoke_agent(client, ROOTCAUSE_AGENT_NAME, str(shipment))
        diagnoses.append({
            "shipment_id": shipment["shipment_id"],
            "severity": shipment["overall_severity"],
            "diagnosis": output_text,
        })
    return diagnoses


def run_erp_reconciliation(client, critical_diagnoses: list) -> list:
    """
    Step 3: CONDITIONAL branch. Only runs for CRITICAL severity.
    This is the piece that isn't in the Factory lab template.
    """
    print("\n=== Step 3: ERP Reconciliation (CRITICAL only) ===")
    if not critical_diagnoses:
        print("  No CRITICAL exceptions — skipping ERP reconciliation.")
        return []

    impacts = []
    for d in critical_diagnoses:
        print(f"  Reconciling {d['shipment_id']} against ERP...")
        output_text = invoke_agent(client, ERP_AGENT_NAME, d["shipment_id"])
        impacts.append({
            "shipment_id": d["shipment_id"],
            "business_impact": output_text,
        })
    return impacts


def generate_cargo_health_report(scan_results: dict, diagnoses: list, impacts: list) -> str:
    print("\n=== Step 4: Cargo Health Report ===")
    lines = [
        "CARGOFLOW SENTINEL - CARGO HEALTH REPORT",
        f"  Shipments checked  : {scan_results['total_checked']}",
        f"  CRITICAL           : {len(scan_results['critical'])}",
        f"  WARNING            : {len(scan_results['warning'])}",
        f"  OK                 : {scan_results['ok_count']}",
        "",
        "DIAGNOSES:",
    ]
    for d in diagnoses:
        lines.append(f"  [{d['severity']}] {d['shipment_id']}: {d['diagnosis']}")

    if impacts:
        lines.append("")
        lines.append("BUSINESS IMPACT (CRITICAL, ERP-reconciled):")
        for i in impacts:
            lines.append(f"  {i['shipment_id']}: {i['business_impact']}")

    report = "\n".join(lines)
    print(report)
    return report


def run_full_workflow():
    ensure_agents_deployed()
    client = _get_client()

    scan_results = run_exception_scan()
    flagged = scan_results["critical"] + scan_results["warning"]

    diagnoses = run_root_cause_diagnosis(client, flagged)

    critical_diagnoses = [d for d in diagnoses if d["severity"] == "CRITICAL"]
    impacts = run_erp_reconciliation(client, critical_diagnoses)

    return generate_cargo_health_report(scan_results, diagnoses, impacts)


if __name__ == "__main__":
    run_full_workflow()
