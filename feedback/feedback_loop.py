"""
CargoFlow Sentinel - Outcome-Based Feedback Loop
==================================================
Pattern B from the offline-eval-vs-production discussion: since live shipments
have no pre-existing "expected_output" the way a curated eval dataset does,
we instead wait for reality to supply the answer, then compare it against
what the agent predicted at the time.

This is NOT a replacement for Challenge 3's offline evaluation (which is
still your pre-deployment quality gate). It's the complementary piece that
answers "is it still accurate now that it's facing real, unseen shipments?"

Run this periodically (e.g. daily, via a scheduled job) against whatever
outcomes have been recorded since the agent's original prediction.
"""

import json
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).resolve().parent
SHIPMENTS_PATH = DATA_DIR.parent / "data" / "shipments.json"
OUTCOMES_PATH = DATA_DIR / "outcomes.json"


def _load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def classify_actual_severity(outcome: dict) -> str:
    """
    Derives what the severity SHOULD have been, based on what actually
    happened. This is the real-world "ground truth" — it didn't exist at
    prediction time, only after the fact.
    """
    if outcome["actual_sla_breach"] or outcome["actual_cold_chain_breach"]:
        return "CRITICAL"
    if outcome["actual_outcome"] in ("delivered_minor_delay",):
        return "WARNING"
    return "OK"


def compare_prediction_to_outcome(outcome: dict) -> dict:
    predicted = outcome["agent_predicted_severity"]
    actual = classify_actual_severity(outcome)

    if predicted == actual:
        match_type = "MATCH"
    elif _severity_rank(predicted) < _severity_rank(actual):
        # Agent under-called it — this is the dangerous direction
        match_type = "FALSE_NEGATIVE"
    else:
        # Agent over-called it — costs attention/resources but not safety
        match_type = "FALSE_POSITIVE"

    return {
        "shipment_id": outcome["shipment_id"],
        "predicted": predicted,
        "actual": actual,
        "match_type": match_type,
    }


def _severity_rank(severity: str) -> int:
    return {"OK": 0, "WARNING": 1, "CRITICAL": 2}.get(severity, 0)


def run_feedback_analysis() -> dict:
    outcomes = _load(OUTCOMES_PATH)["recorded_outcomes"]
    comparisons = [compare_prediction_to_outcome(o) for o in outcomes]

    counts = Counter(c["match_type"] for c in comparisons)
    total = len(comparisons)

    false_negatives = [c for c in comparisons if c["match_type"] == "FALSE_NEGATIVE"]

    print("=" * 60)
    print("CARGOFLOW SENTINEL — OUTCOME-BASED FEEDBACK REPORT")
    print("=" * 60)
    print(f"Shipments reviewed : {total}")
    print(f"  Matches          : {counts['MATCH']} ({counts['MATCH']/total*100:.0f}%)")
    print(f"  False Positives  : {counts['FALSE_POSITIVE']} (agent over-cautious)")
    print(f"  False Negatives  : {counts['FALSE_NEGATIVE']} (agent MISSED a real issue \u2014 priority to fix)")
    print()

    if false_negatives:
        print("FALSE NEGATIVES — review these first, they're the safety-relevant misses:")
        for fn in false_negatives:
            print(f"  {fn['shipment_id']}: predicted {fn['predicted']}, actually {fn['actual']}")
    else:
        print("No false negatives in this batch \u2014 no missed critical issues.")

    print()
    print("These flagged cases are exactly what you'd route to a human reviewer")
    print("to confirm, then fold back into the Challenge 3 eval dataset as new")
    print("labeled examples \u2014 this is how the offline eval set grows more")
    print("representative of real conditions over time (Pattern A + B combined).")

    return {
        "total": total,
        "match_rate": counts["MATCH"] / total,
        "false_negative_rate": counts["FALSE_NEGATIVE"] / total,
        "false_positive_rate": counts["FALSE_POSITIVE"] / total,
        "false_negatives": false_negatives,
    }


if __name__ == "__main__":
    run_feedback_analysis()
