import io
import json
import os
import re
from contextlib import redirect_stdout, redirect_stderr

from autogen import ConversableAgent, UserProxyAgent

from utils.search import search
from utils.mock_data import MOCK_METRICS


# ── Mock mode ──────────────────────────────────────────────────────

MOCK_AUDIENCE = {
    "persona_name": "Style-Conscious Gen Z Dreamer",
    "demographics": "18–24, urban US, multicultural backgrounds, students or early-career creatives",
    "platforms": ["TikTok", "Instagram"],
    "active_hours": "7–11 PM EST weekdays, 10 AM–10 PM weekends",
    "pain_points": [
        "Wants trendy looks on a budget",
        "Feels overwhelmed by fast-fashion choices",
        "Struggles to find authentic style influencers"
    ],
    "content_preferences": [
        "Thrift flips and budget makeovers",
        "GRWM (Get Ready With Me) vlogs",
        "Street style inspiration"
    ],
    "summary": "A budget-conscious Gen Z creative in the city who wants to express personal style without spending a fortune. They follow relatable creators who mix thrift finds with cultural identity."
}

MOCK_STRATEGY = {
    "content_pillars": [
        {"name": "Thrift & Flip", "description": "Affordable thrift finds styled into high-fashion looks", "frequency": "3x/week", "platform": "TikTok"},
        {"name": "Queens Street Style", "description": "Real NYC street fashion featuring diverse styles", "frequency": "2x/week", "platform": "TikTok"},
        {"name": "GRWM on a Budget", "description": "Get-ready-with-me videos showing affordable outfit building", "frequency": "1x/week", "platform": "Instagram"},
        {"name": "Culture & Style", "description": "Style stories rooted in cultural traditions and identity", "frequency": "1x/week", "platform": "Instagram"}
    ],
    "posting_schedule": {
        "TikTok": ["Monday 7:00 PM EST", "Wednesday 8:00 PM EST", "Friday 6:30 PM EST"],
        "Instagram": ["Tuesday 7:00 PM EST", "Thursday 8:00 PM EST"]
    },
    "target_brands": [
        {"name": "Depop", "follower_trigger": "5K followers", "fit_reason": "Thrift-flip content aligns perfectly with Depop's second-hand fashion marketplace", "category": "Fashion Marketplace"},
        {"name": "NA-KD", "follower_trigger": "10K followers", "fit_reason": "Budget-conscious Gen Z style matches their brand identity", "category": "Fashion"},
        {"name": "ThredUp", "follower_trigger": "5K followers", "fit_reason": "Sustainable fashion messaging aligns with thrift content pillars", "category": "Sustainable Fashion"}
    ],
    "six_month_roadmap": [
        {"month": "Month 1-2", "milestone": "Reach 10K followers", "action": "Post 5x/week consistently, engage with niche hashtags"},
        {"month": "Month 3-4", "milestone": "First brand deal inquiry", "action": "Build media kit, pitch to Depop/ThredUp affiliate programs"},
        {"month": "Month 5-6", "milestone": "Monetise with brand partnerships", "action": "Launch Patreon or affiliate links, negotiate paid partnerships"}
    ]
}

MOCK_CONTENT = {
    "scripts": [
        {
            "title": "I Turned an $8 Thrift Jacket Into a $200 Look",
            "pillar": "Thrift & Flip",
            "platform": "TikTok",
            "hook": "You won't believe what I found at the thrift store today...",
            "content": "POV: You walk into a random thrift store in Queens and find an $8 blazer that looks straight off the runway. Here's how I styled it three ways — date night, job interview, and a night out with friends. Which one's your fave?",
            "cta": "Follow for more budget style inspiration!",
            "hashtags": ["#ThriftFlip", "#BudgetStyle", "#NYCFashion", "#SustainableFashion", "#ThriftHaul"]
        },
        {
            "title": "Queens Street Style: Astoria Edition",
            "pillar": "Queens Street Style",
            "platform": "TikTok",
            "hook": "Queens has the BEST street style and I'm proving it.",
            "content": "From 30th Ave to Ditmars, Astoria serves LOOKS. I found 5 people with incredible style and asked them one question: 'What does fashion mean to you?' Their answers will inspire you.",
            "cta": "Tag a friend who needs to see this!",
            "hashtags": ["#QueensStyle", "#NYCStreetStyle", "#Astoria", "#FashionInspo"]
        },
        {
            "title": "GRWM for a Budget Date Night",
            "pillar": "GRWM on a Budget",
            "platform": "Instagram",
            "hook": "Date night but make it affordable 💅",
            "content": "Getting ready for a dinner date with a full look under $60! Thrifted top ($12), high-street jeans ($35), and DIY accessories ($8). Proof that style doesn't need a big budget.",
            "cta": "Save this for your next date night!",
            "hashtags": ["#GRWM", "#BudgetDate", "#AffordableFashion", "#ThriftedOutfit"]
        }
    ],
    "pitch_email": {
        "subject": "Authentic Thrift-Flip Content Creator — Let's Partner!",
        "brand": "Depop",
        "body": "Hi Depop Team,\n\nI'm a NYC-based content creator specialising in thrift-flip fashion and sustainable style. My audience of 6,200+ engaged Gen Z followers loves affordable, eco-conscious fashion — exactly what Depop stands for.\n\nMy thrift-flip videos average 42K views, and my engagement rate is 7.8%. I'd love to collaborate on a campaign showcasing how Depop makes second-hand fashion trendy and accessible.\n\nI have specific content ideas that align with Depop's brand values. Would you be open to a quick call to discuss?\n\nBest,\n[Your Name]"
    }
}

MOCK_PERFORMANCE = {
    "summary": "Strong engagement with Thrift & Flip content outperforming all other pillars. TikTok drives 3x more views than Instagram.",
    "top_content_type": "Thrift & Flip transformation videos (TikTok)",
    "best_posting_time": "Monday 7:00 PM EST",
    "insights": [
        "Thrift Flip content averages 42K views — 2.3x the channel average",
        "Engagement rate of 7.8% is exceptional for a growing creator (industry avg: 3-5%)",
        "Instagram Reels underperforming TikTok — consider cross-posting strategy",
        "Weekend posts show 30% higher save rates than weekday posts"
    ],
    "growth_trend": "Steady upward trajectory — followers growing ~14% month-over-month. Current pace suggests 10K follower milestone in 6-8 weeks."
}

MOCK_OPTIMIZATION = {
    "recommendations": [
        {"action": "Increase Thrift & Flip posts to 4x/week", "reason": "This pillar drives 2.3x average views and highest engagement", "expected_impact": "+35% follower growth rate"},
        {"action": "Move Instagram Reels to weekend posting", "reason": "Weekend posts show 30% higher save rates", "expected_impact": "+20% Instagram engagement"},
        {"action": "Create a weekly series 'Thrift Thursday'", "reason": "Consistent series builds audience habit and algorithm favorability", "expected_impact": "+50% repeat viewership"}
    ],
    "ab_tests": [
        {"test": "Posting time for TikTok Thrift Flips", "variant_a": "Monday 7PM (current)", "variant_b": "Thursday 8PM"},
        {"test": "Video length for Thrift Flips", "variant_a": "60-second cuts", "variant_b": "3-minute storytelling format"},
        {"test": "Instagram Reels vs Carousel posts", "variant_a": "Video format", "variant_b": "Photo carousel with swipe-up"}
    ],
    "quick_wins": [
        "Add a 'series intro' bumper to Thrift Thursday to build brand recognition",
        "Reply to top 3 comments on every post within 1 hour of publishing",
        "Cross-post TikTok Thrift Flips to Instagram Reels with minor edits"
    ]
}

MOCK_PUBLISHING = {
    "weekly_schedule": [
        {"day": "Monday", "time": "7:00 PM EST", "platform": "TikTok", "content_type": "Thrift & Flip", "notification": "📹 Post your Thrift Flip! Don't forget the before/after reveal."},
        {"day": "Tuesday", "time": "7:00 PM EST", "platform": "Instagram", "content_type": "GRWM on a Budget", "notification": "📸 GRWM Reel due today! Keep it authentic and fun."},
        {"day": "Wednesday", "time": "8:00 PM EST", "platform": "TikTok", "content_type": "Queens Street Style", "notification": "🎬 Street style day! Head out and capture the looks."},
        {"day": "Thursday", "time": "8:00 PM EST", "platform": "Instagram", "content_type": "Culture & Style", "notification": "✨ Share your cultural style story — make it personal."},
        {"day": "Friday", "time": "6:30 PM EST", "platform": "TikTok", "content_type": "Thrift & Flip", "notification": "🛍️ Second Thrift Flip of the week! Try a different aesthetic."}
    ],
    "cross_posting_tips": [
        "Trim TikTok vertical videos to 9:16 for Instagram Reels — add subtle caption overlays",
        "Share behind-the-scenes photos from TikTok shoots on Instagram Stories",
        "Use the same hashtag strategy across both platforms for brand consistency"
    ],
    "optimal_frequency": "5 posts/week (3 TikTok + 2 Instagram)"
}

def _is_mock_mode() -> bool:
    """Return True if no real API key is configured."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    return not key or key == "your_openrouter_key_here"

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
    if _is_mock_mode():
        return dict(MOCK_AUDIENCE)
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
    if _is_mock_mode():
        return dict(MOCK_STRATEGY)
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
    if _is_mock_mode():
        return dict(MOCK_CONTENT)
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
    if _is_mock_mode():
        return dict(MOCK_PERFORMANCE)
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
    if _is_mock_mode():
        return dict(MOCK_OPTIMIZATION)
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
    if _is_mock_mode():
        return dict(MOCK_PUBLISHING)
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
