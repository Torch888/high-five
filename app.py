import time
import json
import streamlit as st

from agents.pipeline import run_full_pipeline
from utils.mock_data import MOCK_METRICS

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="CreatorCrew",
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
    ("audience",    "🔍", "Audience Intelligence",  "Profiling your ideal audience..."),
    ("strategy",    "📋", "Content Strategy",       "Building your content plan..."),
    ("content",     "✍️", "Content Generation",     "Drafting your first posts..."),
    ("performance", "📊", "Performance Analyst",    "Analysing engagement patterns..."),
    ("optimization","🎯", "Optimization",           "Finding improvement opportunities..."),
    ("publishing",  "📅", "Publishing & Schedule",  "Setting your posting calendar..."),
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
                Six AI agents. One goal: make you a full-time creator.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.form("onboarding"):
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>QUESTION 1 OF 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>Who are you?</p>",
                unsafe_allow_html=True,
            )
            q1 = st.text_area(
                "Who are you",
                placeholder="Tell us about yourself, your niche, where you're from…",
                height=100,
                key="input_q1",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>QUESTION 2 OF 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>What do you want to create?</p>",
                unsafe_allow_html=True,
            )
            q2 = st.text_area(
                "What do you want to create",
                placeholder="Platforms, formats, topics that excite you…",
                height=100,
                key="input_q2",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                "<p style='color:rgba(255,255,255,0.45);font-size:13px;margin-bottom:2px;'>QUESTION 3 OF 3</p>"
                "<p style='color:white;font-size:19px;font-weight:600;margin-bottom:8px;'>What do you want to achieve?</p>",
                unsafe_allow_html=True,
            )
            q3 = st.text_area(
                "What do you want to achieve",
                placeholder="Brand deals? Full-time creator? Build a community?",
                height=100,
                key="input_q3",
                label_visibility="collapsed",
            )

            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "⚡ Activate My Crew", use_container_width=True, type="primary"
            )

            if submitted:
                if not q1.strip() or not q2.strip() or not q3.strip():
                    st.error("Please answer all three questions to activate your crew.")
                else:
                    st.session_state.q1 = q1
                    st.session_state.q2 = q2
                    st.session_state.q3 = q3
                    st.session_state.page = "activating"
                    st.rerun()

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("🎬  Load Demo — Diana V.", use_container_width=True):
            st.session_state.q1 = (
                "I'm Diana, a Dominican-American fashion creator in Astoria, Queens. "
                "I make content about styling outfits on a real budget — thrift finds, "
                "street style, borough vibes."
            )
            st.session_state.q2 = (
                "I want to post outfit content on TikTok and Instagram, mixing thrift "
                "flips with Queens street style shoots."
            )
            st.session_state.q3 = (
                "I want to land brand deals with fashion brands and eventually go "
                "full-time as a creator."
            )
            st.session_state.page = "activating"
            st.rerun()

        # Agent preview badges
        st.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:rgba(255,255,255,0.3);font-size:12px;text-align:center;"
            "letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;'>Your crew</p>",
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
            <h2 style="color:white;font-size:34px;font-weight:700;margin:0;">Activating Your Crew</h2>
            <p style="color:rgba(255,255,255,0.4);margin-top:8px;">
                Six specialised AI agents are working on your strategy…
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
                    f"<p style='color:rgba(255,255,255,0.15);margin:0;font-size:12px;'>Waiting…</p></div>"
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
                    f"<span style='color:rgba(74,222,128,0.6);font-size:13px;'>✓ Complete</span>"
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
                    f"{name} is working…</p>",
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
            "✓ Your crew is ready!</p>",
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
            "margin-left:14px;'>Dashboard</span></h1>",
            unsafe_allow_html=True,
        )
    with col_reset:
        if st.button("← Start Over", key="reset_top"):
            for k in ["page", "results", "q1", "q2", "q3"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── KPI strip ──────────────────────────────────────────────────
    ov = metrics.get("overview", {})
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Followers",       f"{ov.get('followers', 0):,}", f"+{ov.get('follower_growth_pct', 0)}%")
    k2.metric("Avg Views",       f"{ov.get('avg_views', 0):,}")
    k3.metric("Engagement Rate", f"{ov.get('engagement_rate', 0)}%")
    k4.metric("Avg Shares",      f"{ov.get('avg_shares', 0):,}")

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────────
    tabs = st.tabs([
        "👥 Audience",
        "📋 Strategy",
        "✍️ Content",
        "🤝 Brand Deals",
        "📅 Schedule",
        "📊 Performance",
    ])

    # ── Tab 1: Audience ───────────────────────────────────────────
    with tabs[0]:
        st.markdown("### Your Target Audience")
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
                f"<p style='color:rgba(255,255,255,0.4);font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Demographics</p>"
                f"<p style='color:white;margin-bottom:16px;'>{demo}</p>"
                f"<p style='color:rgba(255,255,255,0.4);font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Most Active</p>"
                f"<p style='color:white;margin:0;'>{hours}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

        with right:
            platforms = audience.get("platforms", [])
            pain_pts  = audience.get("pain_points", [])
            prefs     = audience.get("content_preferences", [])

            if platforms:
                st.markdown("**Platforms**")
                st.write("  ·  ".join(platforms))
            if pain_pts:
                st.markdown("**Pain Points**")
                for p in pain_pts:
                    st.markdown(f"- {p}")
            if prefs:
                st.markdown("**Content Preferences**")
                for p in prefs:
                    st.markdown(f"- {p}")

    # ── Tab 2: Strategy ───────────────────────────────────────────
    with tabs[1]:
        st.markdown("### Content Strategy")

        pillars = strategy.get("content_pillars", [])
        if pillars:
            st.markdown("#### Content Pillars")
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
            st.markdown("#### Posting Schedule")
            sc1, sc2 = st.columns(2)
            for i, (platform, slots) in enumerate(sched.items()):
                col = sc1 if i % 2 == 0 else sc2
                with col:
                    color = "#ff0050" if platform == "TikTok" else "#e1306c"
                    st.markdown(
                        f"<p style='color:{color};font-weight:700;font-size:15px;margin-bottom:6px;'>{platform}</p>",
                        unsafe_allow_html=True,
                    )
                    for slot in slots:
                        st.markdown(f"• {slot}")

        roadmap = strategy.get("six_month_roadmap", [])
        if roadmap:
            st.markdown("#### 6-Month Roadmap")
            for item in roadmap:
                rc1, rc2 = st.columns([1, 4])
                with rc1:
                    st.markdown(f"**{item.get('month', '')}**")
                with rc2:
                    st.markdown(f"🎯 {item.get('milestone', '')}  —  {item.get('action', '')}")

    # ── Tab 3: Content ─────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### Generated Content")
        scripts = content.get("scripts", [])
        if scripts:
            for script in scripts:
                label = f"📱 {script.get('title','Script')}  ·  {script.get('platform','')}"
                with st.expander(label, expanded=False):
                    left, right = st.columns([1, 3])
                    with left:
                        st.markdown(f"**Pillar:** {script.get('pillar','')}")
                        st.markdown(f"**Platform:** {script.get('platform','')}")
                    with right:
                        st.markdown(f"**🎣 Hook**\n\n{script.get('hook','')}")
                        st.markdown(f"**📝 Script**\n\n{script.get('content','')}")
                        st.markdown(f"**📣 CTA:** {script.get('cta','')}")
                        tags = script.get("hashtags", [])
                        if tags:
                            st.markdown("**🏷️ Hashtags:** " + "  ".join(tags))
        else:
            st.info("No scripts generated yet.")

        pitch = content.get("pitch_email", {})
        if pitch:
            st.markdown("---")
            st.markdown("### 📧 Brand Pitch Email")
            st.markdown(f"**To:** {pitch.get('brand','')}")
            st.markdown(f"**Subject:** {pitch.get('subject','')}")
            st.text_area("Email Body", pitch.get("body", ""), height=220, key="pitch_body")

    # ── Tab 4: Brand Deals ─────────────────────────────────────────
    with tabs[3]:
        st.markdown("### Brand Deal Pipeline")
        brands = strategy.get("target_brands", [])
        if brands:
            for brand in brands:
                b1, b2, b3 = st.columns([2, 2, 3])
                with b1:
                    st.markdown(f"**{brand.get('name', '')}**")
                    st.caption(brand.get("category", ""))
                with b2:
                    trigger = brand.get("follower_trigger", "")
                    st.markdown(f"🎯 Reach out at **{trigger}**")
                with b3:
                    st.markdown(brand.get("fit_reason", ""))
                st.divider()
        else:
            st.info("No brand targets generated yet.")

    # ── Tab 5: Schedule ────────────────────────────────────────────
    with tabs[4]:
        toggle_col, _ = st.columns([1, 3])
        with toggle_col:
            auto = st.toggle(
                "⚡ Auto-Publish",
                value=st.session_state.auto_publish,
                key="auto_toggle",
            )
        if auto != st.session_state.auto_publish:
            st.session_state.auto_publish = auto

        if auto:
            st.success("Auto-publish is **ON** — your posts will be queued and published automatically at each scheduled time.")
        else:
            st.info("Auto-publish is **OFF** — you'll receive a notification at each posting time to publish manually.")

        schedule = publishing.get("weekly_schedule", [])
        if schedule:
            st.markdown("### Weekly Posting Calendar")
            for slot in schedule:
                platform = slot.get("platform", "")
                color = "#ff0050" if platform == "TikTok" else "#e1306c"
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
            st.info("Schedule not generated yet.")

        tips = publishing.get("cross_posting_tips", [])
        if tips:
            st.markdown("### Cross-Posting Tips")
            for tip in tips:
                st.markdown(f"• {tip}")

    # ── Tab 6: Performance ─────────────────────────────────────────
    with tabs[5]:
        st.markdown("### Performance Dashboard")
        st.caption("⚠️  Simulated metrics shown for demo purposes — real data updates automatically as you post.")

        posts = metrics.get("posts", [])
        if posts:
            st.markdown("#### Recent Posts")
            for post in posts:
                p1, p2, p3, p4 = st.columns([3, 1, 1, 1])
                with p1:
                    platform = post.get("platform", "")
                    color = "#ff0050" if platform == "TikTok" else "#e1306c"
                    st.markdown(
                        f"**{post['title']}**  "
                        f"<span style='color:{color};font-size:12px;font-weight:600;'>{platform}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption(post.get("pillar", ""))
                with p2:
                    st.metric("Views",  f"{post['views']:,}")
                with p3:
                    st.metric("Likes",  f"{post['likes']:,}")
                with p4:
                    st.metric("Shares", f"{post['shares']:,}")
                st.divider()

        insights = performance.get("insights", [])
        if insights:
            st.markdown("#### AI Insights")
            for ins in insights:
                st.markdown(f"💡 {ins}")

        recs = optimization.get("recommendations", [])
        if recs:
            st.markdown("#### Optimization Recommendations")
            for rec in recs:
                st.markdown(f"**{rec.get('action','')}**")
                st.caption(
                    f"Why: {rec.get('reason','')}  →  Expected: {rec.get('expected_impact','')}"
                )

        wins = optimization.get("quick_wins", [])
        if wins:
            st.markdown("#### Quick Wins")
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
