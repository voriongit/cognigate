"""
INTENT endpoints - Goal processing and normalization.

The INTENT layer interprets and normalizes goals into structured plans.
It surfaces risk and constraint pressure WITHOUT executing actions.
"""

import time
import structlog
from fastapi import APIRouter, HTTPException

from app.models.intent import IntentRequest, IntentResponse, StructuredPlan
from app.models.common import TrustLevel

logger = structlog.get_logger()
router = APIRouter()


# Mock trust database (replace with real service)
MOCK_TRUST_SCORES: dict[str, tuple[int, TrustLevel]] = {
    "agent_001": (450, 2),
    "agent_002": (250, 1),
    "agent_003": (750, 3),
}

# Risk keywords for mock analysis
HIGH_RISK_KEYWORDS = ["delete", "drop", "hack", "exploit", "bypass", "admin", "root", "sudo"]
MEDIUM_RISK_KEYWORDS = ["modify", "update", "change", "write", "send", "transfer"]
TOOL_KEYWORDS = {
    "shell": ["shell", "bash", "cmd", "exec", "run"],
    "file_write": ["write", "save", "create file", "modify file"],
    "file_delete": ["delete", "remove", "rm", "unlink"],
    "network": ["http", "api", "fetch", "request", "curl"],
    "database": ["sql", "query", "select", "insert", "update", "delete from"],
    "email": ["email", "mail", "send message", "notify"],
}


def analyze_intent(goal: str, context: dict) -> StructuredPlan:
    """
    Mock intent analysis - in production, this would use an LLM.
    """
    goal_lower = goal.lower()

    # Detect tools required
    tools_required = []
    for tool, keywords in TOOL_KEYWORDS.items():
        if any(kw in goal_lower for kw in keywords):
            tools_required.append(tool)

    # Calculate risk score
    risk_indicators = {}
    risk_score = 0.1  # Base risk

    # High risk indicators
    high_risk_count = sum(1 for kw in HIGH_RISK_KEYWORDS if kw in goal_lower)
    if high_risk_count > 0:
        risk_indicators["destructive_intent"] = min(0.3 * high_risk_count, 0.9)
        risk_score = max(risk_score, risk_indicators["destructive_intent"])

    # Medium risk indicators
    medium_risk_count = sum(1 for kw in MEDIUM_RISK_KEYWORDS if kw in goal_lower)
    if medium_risk_count > 0:
        risk_indicators["modification_intent"] = min(0.15 * medium_risk_count, 0.5)
        risk_score = max(risk_score, risk_indicators["modification_intent"])

    # Tool-based risk
    if "shell" in tools_required or "file_delete" in tools_required:
        risk_indicators["dangerous_tools"] = 0.7
        risk_score = max(risk_score, 0.7)

    # Data classification (mock)
    data_classifications = []
    if "email" in goal_lower or "@" in goal:
        data_classifications.append("pii_email")
    if "password" in goal_lower or "credential" in goal_lower:
        data_classifications.append("credentials")
    if "ssn" in goal_lower or "social security" in goal_lower:
        data_classifications.append("pii_ssn")

    # Endpoints (mock - extract URLs or domains)
    endpoints_required = []
    if "api" in goal_lower:
        endpoints_required.append("external_api")

    return StructuredPlan(
        goal=goal,
        tools_required=tools_required or ["none"],
        endpoints_required=endpoints_required,
        data_classifications=data_classifications,
        risk_indicators=risk_indicators,
        risk_score=min(risk_score, 1.0),
        reasoning_trace=f"Analyzed intent with {len(tools_required)} tools detected, "
        f"{len(data_classifications)} data types identified, "
        f"risk score: {risk_score:.2f}",
    )


@router.post("/intent", response_model=IntentResponse)
async def normalize_intent(request: IntentRequest) -> IntentResponse:
    """
    Normalize an intent into a structured plan.

    This endpoint:
    1. Receives a raw goal/prompt from an entity
    2. Analyzes and normalizes it into a structured plan
    3. Identifies tools, endpoints, and data types involved
    4. Calculates risk indicators

    The plan is NOT executed - it's passed to ENFORCE for policy validation.
    """
    start_time = time.perf_counter()

    logger.info(
        "intent_received",
        entity_id=request.entity_id,
        goal_length=len(request.goal),
    )

    # Get entity trust (mock)
    trust_score, trust_level = MOCK_TRUST_SCORES.get(
        request.entity_id, (200, 1)  # Default to Provisional
    )

    # Override trust if authorized and provided
    if request.trust_level is not None:
        # In production, verify authorization to override
        trust_level = request.trust_level

    try:
        # Analyze the intent
        plan = analyze_intent(request.goal, request.context)

        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "intent_normalized",
            entity_id=request.entity_id,
            plan_id=plan.plan_id,
            risk_score=plan.risk_score,
            tools=plan.tools_required,
            duration_ms=duration_ms,
        )

        return IntentResponse(
            entity_id=request.entity_id,
            status="normalized",
            plan=plan,
            trust_level=trust_level,
            trust_score=trust_score,
        )

    except Exception as e:
        logger.error(
            "intent_error",
            entity_id=request.entity_id,
            error=str(e),
        )
        return IntentResponse(
            entity_id=request.entity_id,
            status="error",
            trust_level=trust_level,
            trust_score=trust_score,
            error=str(e),
        )


@router.get("/intent/{intent_id}")
async def get_intent(intent_id: str) -> dict:
    """
    Retrieve a previously processed intent by ID.

    In production, this would fetch from a database.
    """
    # Mock - would fetch from database
    raise HTTPException(status_code=404, detail=f"Intent {intent_id} not found")
