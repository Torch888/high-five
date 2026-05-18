import time
import json
import streamlit as st

from agents.pipeline import run_full_pipeline, _is_mock_mode
from utils.mock_data import MOCK_METRICS

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="CreatorCrew - 创作者团队",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0d0d1a 0%, #1a0828 50%, #0d0d1a 100%);
    min-height: 100vh;
}

/* hide default streamlit header chrome */
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; }

/* Cards */
.crew-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
}

/* Agent activation cards */
.agent-idle {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 8px;
    display: flex; align-items: center; gap: 14px;
}
.agent-running {
    background: rgba(147,51,234,0.07);
    border: 1px solid rgba(147,51,234,0.4);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 8px;
}
.agent-done {
    background: rgba(34,197,94,0.05);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 8px;
}

/* Metric override */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: rgba(255,255,255,0.5);
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(147,51,234,0.25) !important;
    color: #c084fc !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c3aed, #db2777);
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 16px;
    padding: 12px;
    color: white;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #6d28d9, #be185d);
    transform: translateY(-1px);
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    color: rgba(255,255,255,0.7);
    font-weight: 500;
}

/* Text inputs */
.stTextArea textarea {
    background: rgba(255,255,255,0.92) !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    border-radius: 10px !important;
    color: #111111 !important;
    font-size: 15px !important;
}
.stTextArea textarea:focus {
    border-color: rgba(147,51,234,0.6) !important;
    box-shadow: 0 0 0 2px rgba(147,51,234,0.15) !important;
}
.stTextArea textarea::placeholder {
    color: rgba(0,0,0,0.4) !important;
}

/* Body text — make all output readable against dark background */
p, li, span, div, label, .stMarkdown, .stMarkdown p, .stMarkdown li {
    color: rgba(255,255,255,0.88) !important;
}
h1, h2, h3, h4, h5, h6 { color: white !important; }

/* Dividers */
hr { border-color: rgba(255,255,255,0.08) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.04) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: white !important;
    font-weight: 500 !important;
}

/* Toggle */
.stToggle { color: white; }

/* Info / success boxes */
.stAlert { border-radius: 10px; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Mock mode indicator ────────────────────────────────────────────
if _is_mock_mode():
    st.sidebar.markdown(
        "<div style='background:#f59e0b20;border:1px solid #f59e0b50;border-radius:8px;"
        "padding:10px 14px;margin-bottom:16px;font-size:13px;'>"
        "🧪 <b>模拟模式</b> — 无 API key，使用模拟数据展示"
        "</div>",
        unsafe_allow_html=True,
    )

# ── Session state defaults ─────────────────────────────────────────
for k, v in {
    "page": "onboarding",
    "results": None,
    "auto_publish": False,
    "q1": "",
    "q2": "",
    "q3": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Agent manifest ─────────────────────────────────────────────────
AGENTS = [
    ("audience",    "🔍", "受众洞察",   "正在分析你的理想受众..."),
    ("strategy",    "📋", "内容策略",   "正在构建你的内容方案..."),
    ("content",     "✍️", "内容生成",   "正在撰写你的首发帖子..."),
    ("performance", "📊", "表现分析",   "正在分析互动数据..."),
    ("optimization","🎯", "优化建议",   "正在寻找改进机会..."),
    ("publishing",  "📅", "发布排期",   "正在设置你的发布日历..."),
]
AGENT_MAP = {k: (icon, name, desc) for k, icon, name, desc in AGENTS}


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — Onboarding
# ══════════════════════════════════════════════════════════════════
def page_onboarding():
    st.markdown(
        """
        <div style="text-align:center; padding: 48px 0 32px 0;">
            <div style="font-size:56px; margin-bottom:12px;">🎨</div>
            <h1 style="color:white; font-size:52px; font-weight:800; margin:0; letter-spacing:-1px;">
                Creator<span style="background:linear-gradient(135deg,#a855f7,#ec4899);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">Crew</span>
            </h1>
            <p style="color:rgba(255,255,255,0.45); font-size:19px; margin-top:10px; font-weight:400;">
                六个 AI 智能体，一个目标：帮你成为全职创作者。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("onboarding"):
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>问题 1 / 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>你是谁？</p>",
                unsafe_allow_html=True,
            )
            q1 = st.text_area(
                "你是谁",
                placeholder="介绍一下你自己、你的领域、来自哪里…",
                height=100,
                key="input_q1",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>问题 2 / 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>你想创作什么？</p>",
                unsafe_allow_html=True,
            )
            q2 = st.text_area(
                "你想创作什么",
                placeholder="平台、形式、让你兴奋的话题…",
                height=100,
                key="input_q2",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>问题 3 / 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>你想达成什么目标？</p>",
                unsafe_allow_html=True,
            )
            q3 = st.text_area(
                "你想达成什么目标",
                placeholder="品牌合作？全职创作者？建立社区？",
                height=100,
                key="input_q3",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "⚡ 激活我的团队", use_container_width=True, type="primary"
            )

            if submitted:
                if not q1.strip() or not q2.strip() or not q3.strip():
                    st.error("请回答全部三个问题以激活你的团队。")
                else:
                    st.session_state.q1 = q1
                    st.session_state.q2 = q2
                    st.session_state.q3 = q3
                    st.session_state.page = "activating"
                    st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("🎬  加载演示 — 小王（时尚创作者）", use_container_width=True):
            st.session_state.q1 = (
                "我是小王，住在上海的时尚创作者。我分享用真实预算搭配穿搭的内容 — "
                "二手好物、街头风格、城市氛围。"
            )
            st.session_state.q2 = (
                "我想在抖音和小红书上发布穿搭内容，把平价好物和街头风格结合起来。"
            )
            st.session_state.q3 = (
                "我想和时尚品牌达成合作，最终成为一名全职创作者。"
            )
            st.session_state.page = "activating"
            st.rerun()

        # Agent preview badges
        st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:rgba(255,255,255,0.3);font-size:12px;text-align:center;"
            "letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;'>你的团队</p>",
            unsafe_allow_html=True,
        )
        badge_cols = st.columns(6)
        for i, (_, icon, name, _) in enumerate(AGENTS):
            with badge_cols[i]:
                st.markdown(
                    f"<div style='text-align:center;'>"
                    f"<div style='font-size:24px;'>{icon}</div>"
                    f"<p style='color:rgba(255,255,255,0.35);font-size:11px;margin-top:4px;line-height:1.3;'>{name}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — Agent Activation
# ══════════════════════════════════════════════════════════════════
def page_activating():
    st.markdown(
        """
        <div style="text-align:center; padding: 40px 0 24px 0;">
            <h2 style="color:white;font-size:34px;font-weight:700;margin:0;">正在激活你的团队</h2>
            <p style="color:rgba(255,255,255,0.4);margin-top:8px;">
                六个专业 AI 智能体正在为你制定策略…
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        placeholders = {k: st.empty() for k, *_ in AGENTS}

        def render_card(key, state):
            icon, name, desc = AGENT_MAP[key]
            if state == "idle":
                placeholders[key].markdown(
                    f"<div class='agent-idle'>"
                    f"<span style='font-size:22px;'>{icon}</span>"
                    f"<div><p style='color:rgba(255,255,255,0.3);margin:0;font-size:15px;'>{name}</p>"
                    f"<p style='color:rgba(255,255,255,0.15);margin:0;font-size:12px;'>等待中…</p></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif state == "running":
                placeholders[key].markdown(
                    f"<div class='agent-running'>"
                    f"<span style='font-size:22px;'>{icon}</span> "
                    f"<span style='color:#c084fc;font-weight:600;font-size:15px;'>{name}</span><br>"
                    f"<span style='color:rgba(192,132,252,0.65);font-size:13px;'>⚡ {desc}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif state == "done":
                placeholders[key].markdown(
                    f"<div class='agent-done'>"
                    f"<span style='font-size:22px;'>{icon}</span> "
                    f"<span style='color:#4ade80;font-weight:600;font-size:15px;'>{name}</span> "
                    f"<span style='color:rgba(74,222,128,0.6);font-size:13px;'>✓ 完成</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        for key, *_ in AGENTS:
            render_card(key, "idle")

        progress = st.progress(0)
        status_msg = st.empty()
        completed = []

        def on_progress(key, state):
            render_card(key, state)
            if state == "running":
                _, name, desc = AGENT_MAP[key]
                status_msg.markdown(
                    f"<p style='color:rgba(255,255,255,0.4);text-align:center;font-size:14px;'>"
                    f"{name} 正在工作中…</p>",
                    unsafe_allow_html=True,
                )
            elif state == "done":
                completed.append(key)
                progress.progress(len(completed) / len(AGENTS))

        results = run_full_pipeline(
            st.session_state.q1,
            st.session_state.q2,
            st.session_state.q3,
            auto_publish=st.session_state.auto_publish,
            progress_callback=on_progress,
        )

        st.session_state.results = results
        status_msg.markdown(
            "<p style='color:#4ade80;text-align:center;font-weight:600;font-size:15px;'>"
            "✓ 你的团队已就绪！</p>",
            unsafe_allow_html=True,
        )
        time.sleep(1)
        st.session_state.page = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — Dashboard
# ══════════════════════════════════════════════════════════════════
def page_dashboard():
    r = st.session_state.results or {}
    audience     = r.get("audience", {})
    strategy     = r.get("strategy", {})
    content      = r.get("content", {})
    performance  = r.get("performance", {})
    optimization = r.get("optimization", {})
    publishing   = r.get("publishing", {})
    metrics      = r.get("mock_metrics", MOCK_METRICS)

    # ── Header ─────────────────────────────────────────────────────
    col_title, col_reset = st.columns([5, 1])
    with col_title:
        st.markdown(
            "<h1 style='color:white;font-size:38px;font-weight:800;margin:0;letter-spacing:-1px;'>"
            "🎨 Creator"
            "<span style='background:linear-gradient(135deg,#a855f7,#ec4899);"
            "-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>Crew</span>"
            "<span style='color:rgba(255,255,255,0.25);font-size:18px;font-weight:400;"
            "margin-left:14px;'>控制台</span></h1>",
            unsafe_allow_html=True,
        )
    with col_reset:
        if st.button("← 重新开始", key="reset_top"):
            for k in ["page", "results", "q1", "q2", "q3"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── KPI strip ──────────────────────────────────────────────────
    ov = metrics.get("overview", {})
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("粉丝数",       f"{ov.get('followers', 0):,}", f"+{ov.get('follower_growth_pct', 0)}%")
    k2.metric("平均观看",       f"{ov.get('avg_views', 0):,}")
    k3.metric("互动率", f"{ov.get('engagement_rate', 0)}%")
    k4.metric("平均分享",      f"{ov.get('avg_shares', 0):,}")

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────────
    tabs = st.tabs([
        "👥 受众",
        "📋 策略",
        "✍️ 内容",
        "🤝 品牌合作",
        "📅 排期",
        "📊 表现",
    ])

    # ── Tab 1: Audience ───────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 目标受众分析")
        left, right = st.columns(2)

        with left:
            persona = audience.get("persona_name", "Your Ideal Audience")
            demo    = audience.get("demographics", "—")
            hours   = audience.get("active_hours", "—")
            summary = audience.get("summary", "")
            st.markdown(
                f"<div class='crew-card'>"
                f"<h3 style='color:#c084fc;margin-top:0;'>✨ {persona}</h3>"
                f"<p style='color:rgba(255,255,255,0.75);'>{summary}</p>"
                f"<hr style='border-color:rgba(255,255,255,0.08);'>"
                f"<p style='color:rgba(255,255,255,0.4);font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>人口统计</p>"
                f"<p style='color:white;margin-bottom:16px;'>{demo}</p>"
                f"<p style='color:rgba(255,255,255,0.4);font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>最活跃时间</p>"
                f"<p style='color:white;margin:0;'>{hours}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with right:
            platforms = audience.get("platforms", [])
            pain_pts  = audience.get("pain_points", [])
            prefs     = audience.get("content_preferences", [])

            if platforms:
                st.markdown("**平台**")
                st.write("  ·  ".join(platforms))
            if pain_pts:
                st.markdown("**痛点**")
                for p in pain_pts:
                    st.markdown(f"- {p}")
            if prefs:
                st.markdown("**内容偏好**")
                for p in prefs:
                    st.markdown(f"- {p}")

    # ── Tab 2: Strategy ───────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 内容策略")

        pillars = strategy.get("content_pillars", [])
        if pillars:
            st.markdown("#### 内容支柱")
            pcols = st.columns(min(len(pillars), 4))
            for i, p in enumerate(pillars[:4]):
                with pcols[i % len(pcols)]:
                    st.markdown(
                        f"<div class='crew-card' style='text-align:center;'>"
                        f"<p style='color:#c084fc;font-weight:700;font-size:16px;margin:0 0 6px;'>{p.get('name','')}</p>"
                        f"<p style='color:rgba(255,255,255,0.55);font-size:13px;margin:0 0 10px;'>{p.get('description','')}</p>"
                        f"<span style='background:rgba(147,51,234,0.2);color:#c084fc;"
                        f"padding:3px 12px;border-radius:20px;font-size:12px;font-weight:500;'>"
                        f"{p.get('frequency','')} · {p.get('platform','')}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        sched = strategy.get("posting_schedule", {})
        if sched:
            st.markdown("#### 发布安排")
            sc1, sc2 = st.columns(2)
            for i, (platform, slots) in enumerate(sched.items()):
                col = sc1 if i % 2 == 0 else sc2
                with col:
                    color = "#ff0050" if platform in ("TikTok", "抖音") else "#e1306c"
                    st.markdown(
                        f"<p style='color:{color};font-weight:700;font-size:15px;margin-bottom:6px;'>{platform}</p>",
                        unsafe_allow_html=True,
                    )
                    for slot in slots:
                        st.markdown(f"• {slot}")

        roadmap = strategy.get("six_month_roadmap", [])
        if roadmap:
            st.markdown("#### 六个月路线图")
            for item in roadmap:
                rc1, rc2 = st.columns([1, 4])
                with rc1:
                    st.markdown(f"**{item.get('month', '')}**")
                with rc2:
                    st.markdown(f"🎯 {item.get('milestone', '')}  —  {item.get('action', '')}")

    # ── Tab 3: Content ─────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 生成内容")
        scripts = content.get("scripts", [])
        if scripts:
            for script in scripts:
                label = f"📱 {script.get('title','脚本')}  ·  {script.get('platform','')}"
                with st.expander(label, expanded=False):
                    left, right = st.columns([1, 3])
                    with left:
                        st.markdown(f"**支柱:** {script.get('pillar','')}")
                        st.markdown(f"**平台:** {script.get('platform','')}")
                    with right:
                        st.markdown(f"**🎣 钩子**\n\n{script.get('hook','')}")
                        st.markdown(f"**📝 脚本**\n\n{script.get('content','')}")
                        st.markdown(f"**📣 行动号召:** {script.get('cta','')}")
                        tags = script.get("hashtags", [])
                        if tags:
                            st.markdown("**🏷️ 标签:** " + "  ".join(tags))
        else:
            st.info("暂无生成脚本。")

        pitch = content.get("pitch_email", {})
        if pitch:
            st.markdown("---")
            st.markdown("### 📧 Brand Pitch Email")
            st.markdown(f"**致:** {pitch.get('brand','')}")
            st.markdown(f"**主题:** {pitch.get('subject','')}")
            st.text_area("邮件正文", pitch.get("body", ""), height=220, key="pitch_body")

    # ── Tab 4: Brand Deals ─────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 品牌合作渠道")
        brands = strategy.get("target_brands", [])
        if brands:
            for brand in brands:
                b1, b2, b3 = st.columns([2, 2, 3])
                with b1:
                    st.markdown(f"**{brand.get('name', '')}**")
                    st.caption(brand.get("category", ""))
                with b2:
                    trigger = brand.get("follower_trigger", "")
                    st.markdown(f"🎯 达到 **{trigger}** 后联系")
                with b3:
                    st.markdown(brand.get("fit_reason", ""))
                st.divider()
        else:
            st.info("暂无品牌目标。")

    # ── Tab 5: Schedule ────────────────────────────────────────────
    with tabs[4]:
        toggle_col, _ = st.columns([1, 3])
        with toggle_col:
            auto = st.toggle(
                "⚡ 自动发布",
                value=st.session_state.auto_publish,
                key="auto_toggle",
            )
        if auto != st.session_state.auto_publish:
            st.session_state.auto_publish = auto

        if auto:
            st.success("自动发布 **已开启** — 你的帖子将在每个预定时间自动排队发布。")
        else:
            st.info("自动发布 **已关闭** — 你会在每个发布时间收到通知并手动发布。")

        schedule = publishing.get("weekly_schedule", [])
        if schedule:
            st.markdown("### 每周发布日历")
            for slot in schedule:
                platform = slot.get("platform", "")
                color = "#ff0050" if platform in ("TikTok", "抖音") else "#e1306c"
                d1, d2, d3, d4 = st.columns([1, 1, 2, 2])
                with d1:
                    st.markdown(f"**{slot.get('day', '')}**")
                with d2:
                    st.markdown(slot.get("time", ""))
                with d3:
                    st.markdown(
                        f"<span style='color:{color};font-weight:600;'>{platform}</span>"
                        f" · {slot.get('content_type','')}",
                        unsafe_allow_html=True,
                    )
                with d4:
                    notif = slot.get("notification", "")
                    if notif:
                        st.caption(f"🔔 {notif}")
                st.divider()
        else:
            st.info("暂无生成排期。")

        tips = publishing.get("cross_posting_tips", [])
        if tips:
            st.markdown("### 跨平台发布建议")
            for tip in tips:
                st.markdown(f"• {tip}")

    # ── Tab 6: Performance ─────────────────────────────────────────
    with tabs[5]:
        st.markdown("### 表现分析面板")
        st.caption("⚠️  模拟数据仅用于演示 — 实际数据会随发帖自动更新。")

        posts = metrics.get("posts", [])
        if posts:
            st.markdown("#### 最近帖子")
            for post in posts:
                p1, p2, p3, p4 = st.columns([3, 1, 1, 1])
                with p1:
                    platform = post.get("platform", "")
                    color = "#ff0050" if platform in ("TikTok", "抖音") else "#e1306c"
                    st.markdown(
                        f"**{post['title']}**  "
                        f"<span style='color:{color};font-size:12px;font-weight:600;'>{platform}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(post.get("pillar", ""))
                with p2:
                    st.metric("观看",  f"{post['views']:,}")
                with p3:
                    st.metric("点赞",  f"{post['likes']:,}")
                with p4:
                    st.metric("分享", f"{post['shares']:,}")
                st.divider()

        insights = performance.get("insights", [])
        if insights:
            st.markdown("#### AI 洞察")
            for ins in insights:
                st.markdown(f"💡 {ins}")

        recs = optimization.get("recommendations", [])
        if recs:
            st.markdown("#### 优化建议")
            for rec in recs:
                st.markdown(f"**{rec.get('action','')}**")
                st.caption(
                    f"原因: {rec.get('reason','')}  →  预期效果: {rec.get('expected_impact','')}"
                )

        wins = optimization.get("quick_wins", [])
        if wins:
            st.markdown("#### 快速取胜")
            for w in wins:
                st.markdown(f"⚡ {w}")


# ══════════════════════════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════════════════════════
page = st.session_state.page
if page == "onboarding":
    page_onboarding()
elif page == "activating":
    page_activating()
elif page == "dashboard":
    page_dashboard()
