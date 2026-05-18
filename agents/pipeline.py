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
    "persona_name": "注重潮流的 Z 世代梦想家",
    "demographics": "18–24岁，城市青年，多元文化背景，学生或初级创意工作者",
    "platforms": ["抖音", "小红书"],
    "active_hours": "工作日晚 7–11 点，周末早 10 点–晚 10 点",
    "pain_points": [
        "预算有限但想穿出潮流感",
        "面对快时尚选择感到迷茫",
        "找不到真实可信的风格博主"
    ],
    "content_preferences": [
        "二手改造和平价穿搭",
        "出门准备（GRWM）视频",
        "街头风格灵感"
    ],
    "summary": "一位注重预算的城市 Z 世代创作者，希望在不花大钱的情况下表达个人风格。他们关注那些能将平价好物与文化自信结合的真实博主。"
}

MOCK_STRATEGY = {
    "content_pillars": [
        {"name": "二手改造", "description": "平价二手好物搭配出高定时装感", "frequency": "3次/周", "platform": "抖音"},
        {"name": "城市街头风格", "description": "真实都市街拍展现多元风格", "frequency": "2次/周", "platform": "抖音"},
        {"name": "预算穿搭", "description": "出门准备视频展示平价穿搭技巧", "frequency": "1次/周", "platform": "小红书"},
        {"name": "文化与风格", "description": "扎根文化传统的风格故事", "frequency": "1次/周", "platform": "小红书"}
    ],
    "posting_schedule": {
        "抖音": ["周一 19:00", "周三 20:00", "周五 18:30"],
        "小红书": ["周二 19:00", "周四 20:00"]
    },
    "target_brands": [
        {"name": "闲鱼", "follower_trigger": "5000 粉丝", "fit_reason": "二手改造内容与闲鱼的闲置交易平台完美契合", "category": "二手交易平台"},
        {"name": "URBAN REVIVO", "follower_trigger": "1万 粉丝", "fit_reason": "注重性价比的时尚风格符合品牌定位", "category": "时尚"},
        {"name": "多抓鱼", "follower_trigger": "5000 粉丝", "fit_reason": "可持续时尚理念与二手改造内容方向一致", "category": "可持续时尚"}
    ],
    "six_month_roadmap": [
        {"month": "第1-2个月", "milestone": "达到 1 万粉丝", "action": "保持每周 5 更，积极参与热门话题"},
        {"month": "第3-4个月", "milestone": "收到第一个品牌合作邀请", "action": "制作媒体工具包，向闲鱼/UR 申请 affiliate 计划"},
        {"month": "第5-6个月", "milestone": "通过品牌合作变现", "action": "推出付费内容或 affiliate 链接，洽谈付费合作"}
    ]
}

MOCK_CONTENT = {
    "scripts": [
        {
            "title": "8 块钱的二手外套穿出 200 块的感觉",
            "pillar": "二手改造",
            "platform": "抖音",
            "hook": "你绝对想不到我今天在二手店淘到了什么…",
            "content": "POV：你在城市街角的二手店花 8 块钱买了一件看起来像高定的外套。我搭了三种风格——约会、面试、和朋友出去浪。你最喜欢哪个？",
            "cta": "关注我获取更多平价穿搭灵感！",
            "hashtags": ["#二手改造", "#平价穿搭", "#城市时尚", "#可持续时尚", "#二手好物"]
        },
        {
            "title": "城市街头风格：老城区特辑",
            "pillar": "城市街头风格",
            "platform": "抖音",
            "hook": "咱们老城区的穿搭真的太绝了，我证明给你看。",
            "content": "从街头到巷尾，老城区到处是穿搭教科书。我找到了 5 个超会穿的人，问了他们同一个问题：'时尚对你来说意味着什么？'他们的回答会让你重新认识穿搭。",
            "cta": "艾特一个需要看这个的朋友！",
            "hashtags": ["#城市风格", "#街拍", "#穿搭灵感"]
        },
        {
            "title": "约会穿搭准备 —— 预算篇",
            "pillar": "预算穿搭",
            "platform": "小红书",
            "hook": "约会要美美的，但不用花大钱 💅",
            "content": "用不到 60 块搞定一整身约会穿搭！二手店里淘的上衣（12 块），高街牛仔裤（35 块），自己 DIY 的配饰（8 块）。证明好品味不一定要贵。",
            "cta": "收藏起来下次约会用！",
            "hashtags": ["#出门准备", "#预算约会", "#平价穿搭", "#二手改造"]
        }
    ],
    "pitch_email": {
        "subject": "真实二手改造内容创作者 —— 期待合作！",
        "brand": "闲鱼",
        "body": "闲鱼团队你们好！\n\n我是一名城市内容创作者，专注于二手改造时尚和可持续风格。我的 6000+ 粉丝喜欢平价又环保的时尚理念——正符合闲鱼的品牌定位。\n\n我的二手改造视频平均观看量 4.2 万，互动率 7.8%。我非常希望能与闲鱼合作，展示二手时尚也可以很潮很亲民。\n\n我有一些具体的合作想法与闲鱼的品牌价值观契合。方便约个时间聊聊吗？\n\n期待回复，\n[你的名字]"
    }
}

MOCK_PERFORMANCE = {
    "summary": "二手改造内容表现强劲，超越所有其他内容支柱。抖音观看量是小红的 3 倍。",
    "top_content_type": "二手改造视频（抖音）",
    "best_posting_time": "周一 19:00",
    "insights": [
        "二手改造内容平均 4.2 万观看 — 是频道平均的 2.3 倍",
        "7.8% 的互动率对成长型创作者来说非常优秀（行业平均 3-5%）",
        "小红书表现不如抖音 — 考虑跨平台发布策略",
        "周末发布的保存率比工作日高 30%"
    ],
    "growth_trend": "稳步上升趋势 — 粉丝每月增长约 14%。按当前速度，预计 6-8 周内达到 1 万粉丝里程碑。"
}

MOCK_OPTIMIZATION = {
    "recommendations": [
        {"action": "将二手改造内容增加到每周 4 次", "reason": "该支柱驱动 2.3 倍平均观看量和最高互动率", "expected_impact": "粉丝增长率 +35%"},
        {"action": "将小红书内容调整到周末发布", "reason": "周末发布的保存率高 30%", "expected_impact": "小红书互动 +20%"},
        {"action": "创建固定栏目「周四改造日」", "reason": "固定栏目建立观众习惯和算法偏好", "expected_impact": "回访观看率 +50%"}
    ],
    "ab_tests": [
        {"test": "抖音二手改造内容发布时间", "variant_a": "周一 19:00（当前）", "variant_b": "周四 20:00"},
        {"test": "二手改造视频长度", "variant_a": "60 秒剪辑版", "variant_b": "3 分钟故事版"},
        {"test": "小红书视频 vs 图文", "variant_a": "视频格式", "variant_b": "图文滑动格式"}
    ],
    "quick_wins": [
        "为「周四改造日」添加固定片头增强品牌识别",
        "每条发布后 1 小时内回复前 3 条评论",
        "将抖音二手改造内容稍作修改后同步发到小红书"
    ]
}

MOCK_PUBLISHING = {
    "weekly_schedule": [
        {"day": "周一", "time": "19:00", "platform": "抖音", "content_type": "二手改造", "notification": "📹 发布改造视频！别忘了改造前后的对比。"},
        {"day": "周二", "time": "19:00", "platform": "小红书", "content_type": "预算穿搭", "notification": "📸 今天要发预算穿搭！保持真实有趣。"},
        {"day": "周三", "time": "20:00", "platform": "抖音", "content_type": "城市街头风格", "notification": "🎬 街头风格日！出门捕捉好看的穿搭。"},
        {"day": "周四", "time": "20:00", "platform": "小红书", "content_type": "文化与风格", "notification": "✨ 分享你的文化风格故事 — 要有个人的温度。"},
        {"day": "周五", "time": "18:30", "platform": "抖音", "content_type": "二手改造", "notification": "🛍️ 本周第二次改造！试试不同的风格。"}
    ],
    "cross_posting_tips": [
        "将抖音竖版视频裁剪为 9:16 发到小红书 — 添加文字说明",
        "把抖音拍摄的花絮照片分享到小红书故事",
        "两个平台使用相同的话题标签策略保持品牌一致性"
    ],
    "optimal_frequency": "每周 5 条（3 条抖音 + 2 条小红书）"
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
