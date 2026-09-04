"""
CargoFlow Sentinel - Agent Build
Three agents: Exception Detection -> Root-Cause & Action -> ERP Reconciliation
(the third is the differentiator vs. the Factory lab's two-agent baseline).

Structure follows microsoft/FrontierWeekHack factory/challenge-1-build/agents.py
Requires: azure-ai-projects, azure-identity, python-dotenv
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential

from tools import CHECK_SHIPMENT_HEALTH_SCHEMA, CHECK_PO_IMPACT_SCHEMA

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

PROJECT_CONNECTION_STRING = os.getenv("PROJECT_CONNECTION_STRING")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4o")

EXCEPTION_AGENT_NAME = "exception-detection-agent"
ROOTCAUSE_AGENT_NAME = "root-cause-action-agent"
ERP_AGENT_NAME = "erp-reconciliation-agent"

EXCEPTION_AGENT_PROMPT = """You are the Exception Detection Agent for CargoFlow Sentinel,
a logistics monitoring system. Your job is ONLY to detect and report exceptions —
never to diagnose causes or recommend actions.

For each shipment you check, use the check_shipment_health tool. Report every
finding with: shipment ID, route, carrier, finding type (delay or cold_chain),
severity (WARNING or CRITICAL), and the specific deviation values.

Be concise and structured. Do not speculate about causes. Do not recommend actions.
That is another agent's job."""

ROOTCAUSE_AGENT_PROMPT = """You are the Root-Cause & Action Agent for CargoFlow Sentinel.
You receive structured exception findings from the Exception Detection Agent
(shipment ID, finding type, severity, deviation values).

For each exception, determine the most likely root cause:
- Delay at customs_clearance stage -> likely customs hold or documentation issue
- Delay at departed_origin stage -> likely carrier scheduling or dock congestion
- Cold-chain (temperature) finding -> likely refrigeration unit fault or prolonged
  customs/dock exposure

Recommend one specific, concrete next action per exception (e.g. "Contact carrier
dispatch for BalticRoute GmbH re: SHP-1003 customs delay", "Flag SHP-1003 for
cold-chain inspection on arrival"). Be specific enough that a logistics coordinator
could act on it immediately without follow-up questions."""

ERP_AGENT_PROMPT = """You are the ERP Reconciliation Agent for CargoFlow Sentinel.
You are only invoked for CRITICAL-severity exceptions, after root-cause diagnosis.

Use the check_po_impact tool to look up the linked purchase order for the shipment.
Translate the technical exception into a business-impact statement for a supply
chain manager: which customer is affected, the order value at risk, whether it
blocks a production line, and the priority level.

If production_dependency is true, explicitly flag this as requiring urgent
escalation, since a factory line may stall. Keep your output to 2-3 sentences,
written for a business audience, not an engineering one."""


def _get_client() -> AIProjectClient:
    return AIProjectClient(
        endpoint=PROJECT_CONNECTION_STRING,
        credential=DefaultAzureCredential(),
    )


def deploy_agents():
    client = _get_client()
    existing = {a.name for a in client.agents.list()}

    shipment_tool = FunctionTool(**CHECK_SHIPMENT_HEALTH_SCHEMA)
    po_tool = FunctionTool(**CHECK_PO_IMPACT_SCHEMA)

    if EXCEPTION_AGENT_NAME not in existing:
        client.agents.create_version(
            agent_name=EXCEPTION_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=EXCEPTION_AGENT_PROMPT,
                tools=[shipment_tool],
            ),
        )
        print(f"Deployed: {EXCEPTION_AGENT_NAME}")
    else:
        print(f"Found existing: {EXCEPTION_AGENT_NAME}")

    if ROOTCAUSE_AGENT_NAME not in existing:
        client.agents.create_version(
            agent_name=ROOTCAUSE_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=ROOTCAUSE_AGENT_PROMPT,
                tools=[],  # reasons over Agent 1's output, no tools needed
            ),
        )
        print(f"Deployed: {ROOTCAUSE_AGENT_NAME}")
    else:
        print(f"Found existing: {ROOTCAUSE_AGENT_NAME}")

    if ERP_AGENT_NAME not in existing:
        client.agents.create_version(
            agent_name=ERP_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=MODEL_DEPLOYMENT_NAME,
                instructions=ERP_AGENT_PROMPT,
                tools=[po_tool],
            ),
        )
        print(f"Deployed: {ERP_AGENT_NAME}")
    else:
        print(f"Found existing: {ERP_AGENT_NAME}")


if __name__ == "__main__":
    deploy_agents()
