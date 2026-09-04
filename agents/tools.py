"""
CargoFlow Sentinel - Tool functions
Bound to the Foundry agents as FunctionTool definitions.
Mirrors the pattern used by check_thresholds in the Factory lab, but for
shipment/logistics data instead of machine sensor data.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Deviation thresholds — tune these for your demo narrative
DELAY_WARNING_HRS = 4.0
DELAY_CRITICAL_HRS = 12.0
TEMP_WARNING_MARGIN_C = 0.5  # within 0.5C of threshold = warning


def _load(filename: str) -> dict:
    with open(DATA_DIR / filename, "r") as f:
        return json.load(f)


def check_shipment_health(shipment_id: str) -> dict:
    """
    Checks a single shipment's milestones and temperature log against
    expected values. Returns structured findings only — no diagnosis.
    This mirrors the Factory lab's check_thresholds() tool.
    """
    shipments = _load("shipments.json")["shipments"]
    shipment = next((s for s in shipments if s["id"] == shipment_id), None)
    if not shipment:
        return {"error": f"Unknown shipment_id: {shipment_id}"}

    findings = []
    max_deviation_hrs = 0.0

    for m in shipment["milestones"]:
        if m["actual_hrs_offset"] is None:
            continue
        deviation = m["actual_hrs_offset"] - m["expected_hrs_offset"]
        max_deviation_hrs = max(max_deviation_hrs, deviation)
        if deviation >= DELAY_CRITICAL_HRS:
            findings.append({
                "type": "delay", "stage": m["stage"], "severity": "CRITICAL",
                "deviation_hrs": round(deviation, 1)
            })
        elif deviation >= DELAY_WARNING_HRS:
            findings.append({
                "type": "delay", "stage": m["stage"], "severity": "WARNING",
                "deviation_hrs": round(deviation, 1)
            })

    temp_log = shipment["temp_log_c"]
    threshold = shipment["temp_threshold_c"]
    max_temp = max(temp_log)
    if max_temp > threshold:
        pct_over = round((max_temp - threshold) / threshold * 100, 1)
        findings.append({
            "type": "cold_chain", "severity": "CRITICAL",
            "max_temp_c": max_temp, "threshold_c": threshold, "pct_over": pct_over
        })
    elif max_temp > threshold - TEMP_WARNING_MARGIN_C:
        findings.append({
            "type": "cold_chain", "severity": "WARNING",
            "max_temp_c": max_temp, "threshold_c": threshold
        })

    overall_severity = "OK"
    if any(f["severity"] == "CRITICAL" for f in findings):
        overall_severity = "CRITICAL"
    elif any(f["severity"] == "WARNING" for f in findings):
        overall_severity = "WARNING"

    return {
        "shipment_id": shipment_id,
        "route": shipment["route"],
        "carrier": shipment["carrier"],
        "overall_severity": overall_severity,
        "findings": findings,
        "linked_po": shipment["linked_po"],
    }


def scan_all_shipments() -> dict:
    """Convenience wrapper: runs check_shipment_health across every shipment."""
    shipments = _load("shipments.json")["shipments"]
    results = [check_shipment_health(s["id"]) for s in shipments]
    return {
        "total_checked": len(results),
        "critical": [r for r in results if r["overall_severity"] == "CRITICAL"],
        "warning": [r for r in results if r["overall_severity"] == "WARNING"],
        "ok_count": len([r for r in results if r["overall_severity"] == "OK"]),
    }


def check_po_impact(shipment_id: str) -> dict:
    """
    ERP Reconciliation Agent's tool. Looks up the linked purchase order
    and returns business-impact context. In a real HSO/D365FO build this
    would call the DMF Package / OData endpoint instead of a JSON lookup.
    """
    shipments = _load("shipments.json")["shipments"]
    shipment = next((s for s in shipments if s["id"] == shipment_id), None)
    if not shipment:
        return {"error": f"Unknown shipment_id: {shipment_id}"}

    pos = _load("purchase_orders.json")["purchase_orders"]
    po = next((p for p in pos if p["po"] == shipment["linked_po"]), None)
    if not po:
        return {"error": f"No PO linked to {shipment_id}"}

    return {
        "shipment_id": shipment_id,
        "po": po["po"],
        "customer": po["customer"],
        "order_value_eur": po["order_value_eur"],
        "production_dependency": po["production_dependency"],
        "priority": po["priority"],
    }


# Foundry FunctionTool schemas (for agent registration in agents.py)
CHECK_SHIPMENT_HEALTH_SCHEMA = {
    "name": "check_shipment_health",
    "description": "Checks a shipment's milestones and cold-chain temperature log against expected thresholds. Returns structured WARNING/CRITICAL findings.",
    "parameters": {
        "type": "object",
        "properties": {
            "shipment_id": {"type": "string", "description": "Shipment ID, e.g. SHP-1003"}
        },
        "required": ["shipment_id"],
    },
}

CHECK_PO_IMPACT_SCHEMA = {
    "name": "check_po_impact",
    "description": "Looks up the purchase order linked to a shipment and returns customer, order value, and production dependency for business-impact assessment.",
    "parameters": {
        "type": "object",
        "properties": {
            "shipment_id": {"type": "string", "description": "Shipment ID, e.g. SHP-1003"}
        },
        "required": ["shipment_id"],
    },
}
