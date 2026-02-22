<p align="center">
  <img src="docs/assets/cover.jpg" alt="MindCast 封面" width="100%" style="max-width:900px; border-radius:12px;" />
</p>

<h1 align="center">MindCast</h1>

<p align="center">
  <strong>多智能体 AI 播客系统 — 任意话题深度解读</strong><br/>
  基于 LangGraph · DeepSeek · MiniMax TTS
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/Vue-3.5+-4FC08D?logo=vue.js&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-0.2+-orange" />
  <img src="https://img.shields.io/badge/license-AGPL--3.0-lightgrey" />
</p>

---

<p align="center">
  <img src="docs/assets/screenshot.png" alt="MindCast 前端截图" width="90%" style="border-radius:8px; border:1px solid #e0e0e0;" />
</p>

---

MindCast 是一个多智能体播客系统，用户输入任意话题后，系统自动从 Tavily 获取最新相关资讯，由主持人 Agent 筛选角度，联合多位不同 MBTI 人格的嘉宾 Agent 生成约 5-15 分钟的播客对话文本，再通过 MiniMax TTS 合成语音并拼接为完整音频。

## 核心特性

| 特性 | 说明 |
|---|---|
| **🤖 多智能体全自动生成** | LangGraph 10 节点流水线：获取资讯 → 选题 → 深度研究 → RAG 检索 → 规划 → 对话 → 文章 → TTS → 拼装 → 保存 |
| **✏️ 两阶段创作模式** | 可先生成纯文稿预览并手动编辑，确认后再触发 TTS 合成；或一键全自动端到端生成 |
| **🎙️ 随机中断机制** | 对话生成时随机激活抢话、接话逻辑，模拟真实播客中的即兴互动 |
| **🧠 RAG 优先研究** | 先查 ChromaDB 知识库，数据新鲜则跳过联网，陈旧才回退 Tavily 实时搜索 |
| **📰 智能去重选题** | 读取近 20 期历史话题，避免重复选题，保持节目新鲜感 |
| **📝 衍生长文生成** | 对话完成后自动生成对应深度文章（存入 `episode.article`） |
| **👥 嘉宾池完整 CRUD** | 前端可增删改嘉宾，AI 可从自然语言描述一键生成完整人设 |
| **🎭 深度去 AI 化** | 系统提示词严格禁止 30+ 种 AI 写作套话（"赋能"、"此外"、"值得注意"等） |
| **🔊 段级音频预览** | 每条对话逐段合成，支持实时播放和段级倍速重新合成 |
| **⚙️ 前端设置面板** | API Keys、LLM 参数可在 UI 直接修改并热重载，无需重启后端 |
| **📡 SSE 实时进度** | 生成全程通过 Server-Sent Events 推送阶段状态，支持任务取消 |
| **🗄️ 知识库管理** | 每期节目可手动或自动导入 ChromaDB，跨期持续沉淀知识 |

---

## 生成流水线

```
Tavily 新闻
    │
    ▼
① fetch_news ──► ② select_topic ──► ③ deep_research
                                           │
                                    RAG-first（ChromaDB）
                                    Tavily fallback（陈旧时）
                                           │
                                           ▼
                                   ④ retrieve_rag
                                           │
                                           ▼
                                   ⑤ plan_episode
                                    （话题 + 大纲 + 冲突设计）
                                           │
                                           ▼
                                   ⑥ generate_dialogue
                                    （多角色轮流 / 随机中断）
                                           │
                                           ▼
                                   ⑦ generate_article
                                    （对话转深度文章）
                                           │
                                           ▼
                                   ⑧ synthesize_tts ──► MiniMax speech-2.8-hd
                                           │
                                           ▼
                                   ⑨ stitch_audio ──► ffmpeg 拼装
                                           │
                                           ▼
                                   ⑩ save_episode ──► output/episodes/{id}.json/.wav
```

---

## 角色人设

| 角色 | 名字 | MBTI | 职业 | 特点 |
|------|------|------|------|------|
| 主持人 | 晨曦 | ENFJ | 科技媒体主编 | 温和引导，善于追问动机 |
| 嘉宾 1 | 兆明 | INTJ | AI 算法工程师 | 数据驱动，喜欢拆解底层逻辑 |
| 嘉宾 2 | 恒宇 | INFP | AI 伦理研究员 | 人文关怀，关注技术的社会代价 |

> 嘉宾池完全可定制：前端可增删改人设，也可用自然语言描述让 AI 自动生成完整角色。

---

## 项目结构

```
MindCast/
├── main.py                  # FastAPI 应用入口 & 启动入口
├── pyproject.toml           # Python 项目配置 & 依赖
├── package.json             # Node 脚本（一键启动 / Docker）
├── Dockerfile               # 后端镜像（多阶段 uv + python:3.13-slim）
├── docker-compose.yml       # 全栈编排（backend + frontend/nginx）
├── .env.example             # 环境变量模板
│
├── backend/                 # 后端源码
│   ├── config.py            # 全局配置（pydantic-settings，支持热重载）
│   ├── models.py            # Pydantic 数据模型
│   ├── agents/              # LangGraph 多智能体
│   │   ├── orchestrator.py  # 主编排图（10 节点流水线）
│   │   ├── host.py          # 主持人 Agent（选题 / 规划 / RAG 决策）
│   │   ├── guest.py         # 嘉宾 Agent（分角色轮流生成对话）
│   │   └── personas.py      # 角色人设 / 系统提示词 / 音色库
│   ├── api/
│   │   ├── routes.py        # 全部 API 路由（含调试端点）
│   │   └── schemas.py       # 请求 / 响应 Schema
│   ├── services/            # 业务服务层
│   │   ├── llm_service.py   # OpenAI-compatible LLM 封装
│   │   ├── tts_service.py   # MiniMax T2A v2 语音合成
│   │   ├── news_service.py  # Tavily 新闻检索
│   │   ├── audio_service.py # pydub + ffmpeg 音频拼装 & 归一化
│   │   ├── guest_pool_service.py  # 嘉宾池 CRUD（data/guest_pool.json）
│   │   ├── host_service.py  # 主持人配置（data/host.json）
│   │   └── run_logger.py    # 每期节目结构化日志（.jsonl）
│   └── knowledge/           # RAG / ChromaDB 知识库接口
│
├── frontend/                # Vue 3 + Vite 前端
│   ├── Dockerfile           # 多阶段构建 → nginx:alpine 服务
│   ├── nginx.conf           # SPA + /api 反代到 backend 服务
│   └── src/
│       ├── views/           # Home（工作流）、Episode（详情页）
│       ├── components/      # WorkflowWizard / GuestDrawer / PodcastPlayer …
│       └── stores/          # Pinia 全局状态
│
├── tests/                   # 后端单元测试（pytest）
├── scripts/
│   └── run_text_pipeline.py # 仅文本模式（跳过 TTS，快速调试）
│
├── data/                    # 本地持久化
│   ├── guest_pool.json      # 嘉宾池
│   ├── host.json            # 主持人配置
│   └── chromadb/            # ChromaDB 向量库（gitignored）
├── output/episodes/         # 已生成的节目（gitignored）
└── docs/
    ├── assets/              
    └── 深度播客访谈特质研究.md
```

---

## 快速开始

### 前置依赖

| 依赖 | 要求 | 用途 |
|------|------|------|
| Python | ≥ 3.13 | 后端运行时 |
| uv | 最新版 | Python 依赖管理 |
| Node.js | ≥ 18 | 前端开发 & npm 脚本 |
| ffmpeg | 系统安装，需在 PATH | 音频拼装与归一化 |
| Docker + Compose v2 | 可选 | 容器化部署 |

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入以下 API Keys：
#   LLM_API_KEY      — DeepSeek / 任何 OpenAI-compatible 服务
#   TAVILY_API_KEY   — tavily.com（新闻检索）
#   MINIMAX_API_KEY  — minimaxi.com（TTS 语音合成）
```

> 也可在启动后通过前端「设置」面板填写，会自动写入 `.env` 并热重载，无需重启。

---

### 方式一：本地开发（推荐）

```bash
# 1. 一键安装所有依赖（仅首次）
npm run setup:all

# 2. 同时启动前后端（彩色日志区分）
npm run dev
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| Swagger 文档 | http://localhost:8000/docs |

**分步启动：**

```bash
npm run backend    # 仅后端
npm run frontend   # 仅前端
```

---

### 方式二：Docker

```bash
# 构建并启动（首次约 2–3 分钟）
npm run docker:up
# 等价于：docker compose up --build

# 查看实时日志
npm run docker:logs

# 停止
npm run docker:down
```

启动后访问 **http://localhost**（80 端口），nginx 自动将 `/api` 请求代理到后端容器。

> **注意**：`.env` 文件会通过 `env_file` 挂载到后端容器，生产部署前请确保 API Keys 已配置。

---

### 方式三：纯 Python 脚本

```bash
uv sync
# 命令行运行完整流水线（跳过 TTS / 音频，快速验证）
uv run python scripts/run_text_pipeline.py
```
