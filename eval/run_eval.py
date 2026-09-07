"""
CargoFlow Sentinel - Evaluation
Runs an LLM-as-judge evaluation against eval_dataset.json, following the
same pattern as the Factory lab's Challenge 3 (Evaluate). Keep the JSON
output — it's your evidence for the "we measured quality" story on
presentation day.
"""

import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents"))

from agents import _get_client, invoke_agent, ROOTCAUSE_AGENT_NAME, ERP_AGENT_NAME  # noqa: E402

EVAL_DATA_PATH = Path(__file__).resolve().parent / "eval_dataset.json"
RESULTS_PATH = Path(__file__).resolve().parent / "eval_results.json"

JUDGE_PROMPT_TEMPLATE = """You are grading an AI agent's diagnosis output for quality.

Input finding given to the agent:
{input_finding}

Agent's actual output:
{actual_output}

Expected the output to reasonably contain concepts like: {expected_terms}
Expected the recommended action to be specific and actionable: {expected_specific}

Score from 1-5 (5 = excellent, matches expectations closely and is actionable;
1 = poor, generic or misses the core issue). Respond with ONLY a JSON object:
{{"score": <int>, "reasoning": "<one sentence>"}}
"""


def judge(client, judge_model: str, input_finding: str, actual_output: str,
          expected_terms: list, expected_specific: bool) -> dict:
    prompt = JUDGE_PROMPT_TEMPLATE.format(
        input_finding=input_finding,
        actual_output=actual_output,
        expected_terms=", ".join(expected_terms),
        expected_specific=expected_specific,
    )
    output_text = invoke_agent(client, judge_model, prompt)
    try:
        return json.loads(output_text)
    except json.JSONDecodeError:
        return {"score": None, "reasoning": "Could not parse judge output", "raw": output_text}


def run_evaluation():
    with open(EVAL_DATA_PATH) as f:
        test_cases = json.load(f)["test_cases"]

    client = _get_client()
    results = []

    for case in test_cases:
        is_erp_case = case["shipment_id"].endswith("-erp")
        agent_name = ERP_AGENT_NAME if is_erp_case else ROOTCAUSE_AGENT_NAME

        actual_output = invoke_agent(client, agent_name, case["input_finding"])
        verdict = judge(
            client,
            judge_model=ROOTCAUSE_AGENT_NAME,  # reuse as judge, or point at a dedicated eval model
            input_finding=case["input_finding"],
            actual_output=actual_output,
            expected_terms=case["expected_diagnosis_contains"],
            expected_specific=case["expected_action_specific"],
        )
        results.append({
            "shipment_id": case["shipment_id"],
            "actual_output": actual_output,
            "score": verdict.get("score"),
            "reasoning": verdict.get("reasoning"),
        })
        print(f"{case['shipment_id']}: score={verdict.get('score')} - {verdict.get('reasoning')}")

    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    scores = [r["score"] for r in results if r["score"] is not None]
    avg = sum(scores) / len(scores) if scores else 0
    print(f"\nAverage score: {avg:.2f} / 5  (results saved to {RESULTS_PATH})")


if __name__ == "__main__":
    run_evaluation()
