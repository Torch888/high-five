# CreatorCrew 🎨 — 创作者团队

**六个 AI 智能体，一个目标：帮你成为全职创作者。**

CreatorCrew 是一个为内容创作者打造的多智能体 AI 平台。描述你自己、你的内容和你的目标 —— 六个专业 AI 智能体将为你构建完整的创作者策略，只需几分钟。

---

## 功能简介

CreatorCrew 依次运行六个 AG2 智能体，各自负责创作者旅程的不同环节：

| 智能体 | 职责 |
|--------|------|
| 🔍 受众洞察 | 分析你的理想目标受众画像 |
| 📋 内容策略 | 构建内容支柱、发布计划和品牌路线图 |
| ✍️ 内容生成 | 撰写可直接发布的抖音/小红书脚本和品牌合作邮件 |
| 📊 表现分析 | 解读互动数据，挖掘核心洞察 |
| 🎯 优化建议 | 将数据转化为优先级改进方案和 A/B 测试 |
| 📅 发布排期 | 创建每周发布日历和提醒 |

---

## 技术栈

- **[AG2](https://github.com/ag2ai/ag2)** — 多智能体 AI 框架（ConversableAgent + UserProxyAgent）
- **Google Gemini 2.5 Flash** via OpenRouter
- **Tavily** — 实时网络搜索用于受众和品牌调研
- **Streamlit** — Web UI，暗色紫粉主题
- **Python 3.11+**

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Torch888/high-five.git
cd high-five
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置 API 密钥（可选）

创建 `.env` 文件（不配置也能运行，会自动使用模拟模式）：

```
OPENROUTER_API_KEY=your_openrouter_key_here
TAVILY_API_KEY=your_tavily_key_here
```

> **💡 模拟模式：** 如果没有 API 密钥，应用会自动进入模拟模式，使用预设的中文模拟数据展示全部功能。侧边栏会显示"模拟模式"标识。

### 5. 运行应用

```bash
streamlit run app.py
```

---

## 项目结构

```
high-five/
├── app.py                  # Streamlit UI（引导页 → 激活中 → 控制台）
├── agents/
│   ├── config.py           # LLM 配置（OpenRouter / Gemini）
│   └── pipeline.py         # 6 个智能体 + 编排器 + 模拟数据
├── utils/
│   ├── search.py           # Tavily 网络搜索封装
│   └── mock_data.py        # 模拟互动数据（中文）
├── requirements.txt
└── .streamlit/
    └── config.toml
```

---

## 关于本项目

本项目基于 AG2 Hackathon（纽约，2026 年 5 月）的获奖项目 **CreatorCrew** 改造而来。

### 本仓库的改进

- 🌐 **全界面中文化** — 所有 UI 文字、模拟数据均已翻译为中文
- 🧪 **模拟模式** — 无需 API 密钥即可体验全部功能
- 📱 **平台适配** — 针对抖音/小红书等国内平台进行了调整

---

## 部署

应用可部署在 **Streamlit Cloud** 上。密钥通过 Streamlit Cloud 的 Secrets 管理。

---

## 致谢

- 原作团队：Shageenth Sandrakumar, Miriam Contino, TaliZ, Susan
- AG2 Hackathon — New York City, May 2026
