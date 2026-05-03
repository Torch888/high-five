import io
import json
import re
from contextlib import redirect_stdout, redirect_stderr

from autogen import ConversableAgent, UserProxyAgent

from utils.search import search
from utils.mock_data import MOCK_METRICS


# ── Helpers ────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    """Extract the first JSON object from an agent response."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"raw": text}


def _call_agent(name: str, system_message: str, task: str) -> str:
    """Spin up one AG2 agent, get a single response, return it."""
    from agents.config import get_llm_config
    agent = ConversableAgent(
        name=name,
        system_message=system_message,
        llm_config=get_llm_config(),
        human_input_mode="NEVER",
    )
    proxy = UserProxyAgent(
        name="CreatorCrew_Orchestrator",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0,
        code_execution_config=False,
        is_termination_msg=lambda _: True,
    )

    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(buf):
        result = proxy.initiate_chat(agent, message=task, max_turns=1)

    # ChatResult.chat_history — last entry is the agent reply
    if result and hasattr(result, "chat_history") and result.chat_history:
        last = result.chat_history[-1]
        content = last.get("content", "")
        if content:
            return content

    # proxy stores agent messages keyed by agent object; last item is agent reply
    msgs = proxy.chat_messages.get(agent, [])
    if msgs:
        return msgs[-1].get("content", "")

    # agent stores its own messages keyed by proxy
    msgs = agent.chat_messages.get(proxy, [])
    if msgs:
        return msgs[-1].get("content", "")

    return buf.getvalue()  # last resort: captured stdout


# ── Agent 1: Audience Intelligence ────────────────────────────────

def run_audience_agent(q1: str, q2: str, q3: str) -> dict:
    web_context = search(f"content creator audience demographics niche {q1[:80]}")

    system_msg = """You are the Audience Intelligence Agent for CreatorCrew — a multi-agent AI platform for content creators.
Your job: analyse a creator's self-description and derive their ideal target audience persona.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "persona_name": "A catchy name for the audience segment",
  "demographics": "Age range, location, cultural background, lifestyle snapshot",
  "platforms": ["platform1", "platform2"],
  "active_hours": "Peak online times with timezone",
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "content_preferences": ["preference 1", "preference 2", "preference 3"],
  "summary": "2-3 sentence narrative portrait of this audience"
}
```"""

    task = f"""Analyse this creator and identify their ideal target audience:

Who they are: {q1}
What they want to create: {q2}
Their goals: {q3}

Web research context:
{web_context}

Return the audience profile as a JSON object."""

    return _parse_json(_call_agent("AudienceIntelligence", system_msg, task))


# ── Agent 2: Content Strategy ──────────────────────────────────────

def run_strategy_agent(q1: str, q2: str, q3: str, audience: dict) -> dict:
    brand_search = search(f"fashion brands brand deals influencer collab {q1[:60]}")

    system_msg = """You are the Content Strategy Agent for CreatorCrew.
Your job: turn an audience profile into a complete, actionable content strategy.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "content_pillars": [
    {"name": "Pillar Name", "description": "What this covers", "frequency": "Nx/week", "platform": "TikTok/Instagram/Both"}
  ],
  "posting_schedule": {
    "TikTok": ["Day HH:MM AM/PM EST", "Day HH:MM AM/PM EST"],
    "Instagram": ["Day HH:MM AM/PM EST", "Day HH:MM AM/PM EST"]
  },
  "target_brands": [
    {"name": "Brand", "follower_trigger": "Xk followers", "fit_reason": "Why they are a match", "category": "Fashion/Lifestyle/etc"}
  ],
  "six_month_roadmap": [
    {"month": "Month 1-2", "milestone": "Concrete goal", "action": "What to do to hit it"}
  ]
}
```"""

    task = f"""Build a full content strategy for this creator:

Creator: {q1}
Content intent: {q2}
Business goals: {q3}

Target audience profile:
{json.dumps(audience, indent=2)}

Brand research context:
{brand_search}

Return the complete strategy as a JSON object."""

    return _parse_json(_call_agent("ContentStrategy", system_msg, task))


# ── Agent 3: Content Generation ────────────────────────────────────

def run_content_agent(q1: str, audience: dict, strategy: dict) -> dict:
    pillars = strategy.get("content_pillars", [])
    pillar_names = [p.get("name", "") for p in pillars[:3]]
    brands = strategy.get("target_brands", [])
    first_brand = brands[0].get("name", "Depop") if brands else "Depop"

    system_msg = """You are the Content Generation Agent for CreatorCrew.
Your job: write ready-to-post TikTok/Instagram content that sounds 100% authentic to the creator's voice.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "scripts": [
    {
      "title": "Post title",
      "pillar": "Content pillar name",
      "platform": "TikTok or Instagram",
      "hook": "Opening line — must grab attention in the first 3 seconds",
      "content": "Full script or caption body",
      "cta": "Clear call to action",
      "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
    }
  ],
  "pitch_email": {
    "subject": "Subject line",
    "brand": "Brand name",
    "body": "Full pitch email text — personalised, concise, confident"
  }
}
```"""

    task = f"""Write content for this creator:

Creator info: {q1}
Audience summary: {audience.get("summary", "")}
Content pillars to cover: {", ".join(pillar_names)}

Write 3 scripts — one per pillar — for TikTok or Instagram.
Also write a brand pitch email to {first_brand}.

Match the creator's authentic voice based on how they described themselves.
Return as a JSON object."""

    return _parse_json(_call_agent("ContentGeneration", system_msg, task))


# ── Agent 4: Performance Analyst ───────────────────────────────────

def run_performance_agent() -> dict:
    system_msg = """You are the Performance Analyst Agent for CreatorCrew.
Your job: interpret engagement data and surface the insights that matter most to a growing creator.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "summary": "One paragraph overview of current performance",
  "top_content_type": "The content format or pillar driving the most engagement",
  "best_posting_time": "The single best time to post based on data",
  "insights": ["Specific insight 1", "Specific insight 2", "Specific insight 3"],
  "growth_trend": "Description of follower and engagement trajectory"
}
```"""

    task = f"""Analyse these TikTok and Instagram performance metrics:

{json.dumps(MOCK_METRICS, indent=2)}

Identify patterns, top-performing content types, and the most actionable insights for a growing fashion creator.
Return your analysis as a JSON object."""

    return _parse_json(_call_agent("PerformanceAnalyst", system_msg, task))


# ── Agent 5: Optimization ──────────────────────────────────────────

def run_optimization_agent(performance: dict, strategy: dict) -> dict:
    system_msg = """You are the Optimization Agent for CreatorCrew.
Your job: turn performance insights into specific, prioritised improvements to the content strategy.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "recommendations": [
    {"action": "What to change", "reason": "Why the data supports this", "expected_impact": "What metric will improve"}
  ],
  "ab_tests": [
    {"test": "What to test", "variant_a": "Option A", "variant_b": "Option B"}
  ],
  "quick_wins": ["Quick win 1", "Quick win 2", "Quick win 3"]
}
```"""

    task = f"""Optimise this creator's strategy based on real performance data:

Performance analysis:
{json.dumps(performance, indent=2)}

Current strategy:
{json.dumps(strategy, indent=2)}

Suggest specific, prioritised improvements. Be concrete — reference the actual data.
Return as a JSON object."""

    return _parse_json(_call_agent("Optimization", system_msg, task))


# ── Agent 6: Publishing & Schedule ────────────────────────────────

def run_publishing_agent(strategy: dict, auto_publish: bool = False) -> dict:
    system_msg = """You are the Publishing & Schedule Agent for CreatorCrew.
Your job: build a detailed weekly posting calendar with notification messages for each slot.

Always respond with ONLY a JSON object inside a ```json code block. No extra text.
Required structure:
```json
{
  "weekly_schedule": [
    {
      "day": "Monday",
      "time": "7:00 PM EST",
      "platform": "TikTok",
      "content_type": "Pillar name",
      "notification": "Short reminder message the creator will see"
    }
  ],
  "cross_posting_tips": ["tip 1", "tip 2", "tip 3"],
  "optimal_frequency": "Recommended total posts per week"
}
```"""

    task = f"""Build a weekly posting schedule based on:

Recommended posting times:
{json.dumps(strategy.get("posting_schedule", {}), indent=2)}

Content pillars:
{json.dumps(strategy.get("content_pillars", []), indent=2)}

Mode: {"AUTO-PUBLISH ENABLED — include scheduling confirmation messages" if auto_publish else "NOTIFICATIONS ONLY — write reminder messages the creator will act on manually"}

Return a complete 7-day schedule (only include days with posts) as a JSON object."""

    return _parse_json(_call_agent("PublishingSchedule", system_msg, task))


# ── Main orchestrator ──────────────────────────────────────────────

def run_full_pipeline(
    q1: str,
    q2: str,
    q3: str,
    auto_publish: bool = False,
    progress_callback=None,
) -> dict:
    """Run all 6 CreatorCrew agents sequentially and return the full results dict."""

    def update(agent_key: str, status: str):
        if progress_callback:
            progress_callback(agent_key, status)

    results = {}

    update("audience", "running")
    results["audience"] = run_audience_agent(q1, q2, q3)
    update("audience", "done")

    update("strategy", "running")
    results["strategy"] = run_strategy_agent(q1, q2, q3, results["audience"])
    update("strategy", "done")

    update("content", "running")
    results["content"] = run_content_agent(q1, results["audience"], results["strategy"])
    update("content", "done")

    update("performance", "running")
    results["performance"] = run_performance_agent()
    results["mock_metrics"] = MOCK_METRICS
    update("performance", "done")

    update("optimization", "running")
    results["optimization"] = run_optimization_agent(
        results["performance"], results["strategy"]
    )
    update("optimization", "done")

    update("publishing", "running")
    results["publishing"] = run_publishing_agent(results["strategy"], auto_publish)
    update("publishing", "done")

    return results
