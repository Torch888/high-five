# CreatorCrew 🎨

**Six AI agents. One goal: make you a full-time creator.**

CreatorCrew is a multi-agent AI platform built for content creators. Describe yourself, your content, and your goals — and a crew of six specialised agents will build your complete creator strategy in minutes.

Live app: [https://high-five-qknaby4vc4w5zqstwsmcgk.streamlit.app](https://high-five-qknaby4vc4w5zqstwsmcgk.streamlit.app)

---

## What It Does

CreatorCrew runs six AG2 agents in sequence, each tackling a different part of the creator journey:

| Agent | Role |
|---|---|
| 🔍 Audience Intelligence | Profiles your ideal target audience |
| 📋 Content Strategy | Builds your content pillars, posting schedule, and brand roadmap |
| ✍️ Content Generation | Writes ready-to-post TikTok/Instagram scripts and a brand pitch email |
| 📊 Performance Analyst | Interprets engagement metrics and surfaces key insights |
| 🎯 Optimization | Turns data into prioritised improvements and A/B tests |
| 📅 Publishing & Schedule | Creates a weekly posting calendar with reminders |

---

## Tech Stack

- **[AG2](https://github.com/ag2ai/ag2)** — multi-agent AI framework (ConversableAgent + UserProxyAgent)
- **Google Gemini 2.5 Flash** via OpenRouter
- **Tavily** — live web search for audience and brand research
- **Streamlit** — web UI with a dark purple/pink theme
- **Python 3.11**

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/shageenthsandrakumar/high-five.git
cd high-five
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API keys

Create a `.env` file in the project root:

```
OPENROUTER_API_KEY=your_openrouter_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### 5. Run the app

```bash
streamlit run app.py
```

---

## Project Structure

```
high-five/
├── app.py                  # Streamlit UI (onboarding → activating → dashboard)
├── agents/
│   ├── config.py           # LLM config (OpenRouter / Gemini)
│   └── pipeline.py         # All 6 agents + orchestrator
├── utils/
│   ├── search.py           # Tavily web search wrapper
│   └── mock_data.py        # Simulated TikTok/Instagram metrics
├── requirements.txt
└── .streamlit/
    └── config.toml
```

---

## How We Built It
We built CreatorCrew in one day at the AG2 Hackathon in NYC. The core of the app is a six-agent pipeline powered by AG2 (formerly AutoGen), where each agent has a single responsibility — from profiling the audience to generating scripts to scheduling posts. We used Google Gemini 2.5 Flash via OpenRouter as the LLM backbone, Tavily for live web search to ground the agents in real data, and Streamlit to ship a polished UI fast.

---

## Demo & Screenshots

<!-- ✏️ SUSAN — add a short description of the demo flow here, or paste in a screenshot link. Then commit it! -->

---

## Meet the Team

**Shageenth Sandrakumar** — Project Co-Lead. Built and deployed the entire CreatorCrew application, architected the six-agent AG2 pipeline, and managed the end-to-end technical execution.

**Miriam Contino** — Co-created the pitch presentation, produced the demo video, and contributed 35% of the Product Requirements Document.

**TaliZ** — Project Co-Lead. Project Ideation, created the pitch presentation and contributed 30% of the Product Requirements Document.

**Susan** — Contributed 35% of the Product Requirements Document.

---

## Deployment

The app is deployed on **Streamlit Cloud**. Secrets are managed via the Streamlit Cloud UI

---

## Built At

AG2 Hackathon — New York City, May 2026
