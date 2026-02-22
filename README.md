# MindCast

> 多智能体播客生成器 — 任意话题深度解读

MindCast 是一个多智能体播客系统，用户输入任意话题后，系统自动从 Tavily 获取最新相关资讯，由主持人 Agent 筛选角度，联合多位不同 MBTI 人格的嘉宾 Agent 生成约 5 分钟的播客对话文本，再通过 MiniMax `speech-2.8-hd` 合成语音并拼接为完整音频。

## 核心特性

- **🤖 多智能体协同**：基于 LangGraph 构建的复杂工作流，包含主持人、技术专家、创业者及伦理学家四种人格角色。
- **🎙️ 自然对话模拟**：内置高拟真对话引擎，支持**随机中断机制**与上下文关联，模拟真实播客中的即兴互动。
- **🧠 记忆与 RAG**：集成 **ChromaDB** 向量数据库，自动检索往期节目上下文、专家知识库及事实核查信息，确保持续演进的知识深度。
- **🎭 深度“去 AI 化”**：自研人文化提示词框架，严格过滤 AI 常用术语与刻板结构，打造极具辨识度的角色个性。
- **🔍 开发者友好**：全链路结构化日志，每期生成均有独立的 `.jsonl` 审计追踪，支持对话过程的深度回溯。

## 架构

- **后端**：FastAPI + LangGraph + OpenAI-compatible LLM + Tavily + MiniMax TTS
- **向量库**：ChromaDB (用于知识检索增强 RAG)
- **前端**：Vue 3 + Vite
- **Agent 系统**：news → topic → research → rag_retrieval → planning → dialogue → tts → audio
- **可观测性**：集中化日志管理，支持每期生成的 File-based 调试记录。

## 项目结构

```
MindCast/
├── main.py                  # FastAPI 应用入口
├── pyproject.toml           # Python 项目配置 & 依赖
├── package.json             # Node 脚本（一键启动前后端）
├── .env.example             # 环境变量模板
│
├── backend/                 # 后端源码
│   ├── config.py            # 全局配置（pydantic-settings）
│   ├── models.py            # Pydantic 数据模型
│   ├── logging_config.py
│   ├── agents/              # LangGraph 多智能体
│   │   ├── orchestrator.py  # 主编排图
│   │   ├── host.py          # 主持人 Agent
│   │   ├── guest.py         # 嘉宾 Agent
│   │   └── personas.py      # 角色人设 / 系统提示词
│   ├── api/                 # FastAPI 路由层
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── services/            # 业务服务（LLM / TTS / News…）
│   └── knowledge/           # RAG / ChromaDB 知识库接口
│
├── frontend/                # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   └── stores/          # Pinia 状态管理
│   └── package.json
│
├── tests/                   # 后端单元测试
├── scripts/                 # 开发辅助脚本
│   └── run_text_pipeline.py # 仅文本模式（跳过 TTS）
│
├── data/                    # 本地持久化数据
│   ├── guest_pool.json      # 嘉宾池
│   ├── host.json            # 主持人配置
│   └── chromadb/            # ChromaDB 向量库（gitignored）
├── output/episodes/         # 已生成的节目（gitignored）
└── docs/                    # 文档 & 设计资产
    ├── assets/              # 封面图、截图等
    └── 深度播客访谈特质研究.md
```

## 角色

| 角色 | 名字 | MBTI | 职业 |
|------|------|------|------|
| 主持人 | 林晨曦 | ENFJ | 科技媒体主编 |
| 嘉宾 1 | 赵明远 | INTJ | AI 算法工程师 |
| 嘉宾 2 | 苏婉清 | ENTP | AI 创业者 |
| 嘉宾 3 | 陈志恒 | INFP | AI 伦理研究员 |

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 API Keys，也可以在前端界面输入
```

### 2. 一键安装所有依赖

```bash
npm run setup:all
```

> 等价于依次执行：`npm install`（根目录）、`cd frontend && npm install`、`uv sync`。

### 3. 一键启动前后端

```bash
npm run dev
```

后端默认运行于 `http://localhost:8000`，前端默认运行于 `http://localhost:5173`。

---

**分步启动（可选）**

```bash
# 仅启动后端
npm run backend

# 仅启动前端
npm run frontend
```

如需自定义前端代理目标：

```bash
# Windows PowerShell
$env:VITE_API_TARGET="http://127.0.0.1:8000"
npm run frontend
```

### 4. 使用

- 访问 `http://localhost:5173` 打开前端
- 点击 "获取今日资讯"，从资讯中选择话题（或输入自定义话题）
- 在页面中增删改嘉宾池信息，并从嘉宾池勾选本期嘉宾（最多 3 位）
- 点击 "开始生成" 或先 "生成文稿" 再 "确认并合成"
- 等待生成完成后即可收听

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/generate` | POST | 触发生成新一期播客 |
| `/api/episodes` | GET | 获取已生成的播客列表 |
| `/api/episodes/{id}` | GET | 获取某期详情 |
| `/api/episodes/{id}/audio` | GET | 返回音频文件流 |
| `/api/status/{task_id}` | GET (SSE) | 生成进度实时推送 |
| `/api/knowledge/stats` | GET | 获取知识库集合统计信息 |
| `/api/knowledge/query` | POST | 检索知识库相关背景资料 |
| `/api/knowledge/ingest-episode/{id}` | POST | 手动导入特定节目到知识库 |

## 前置依赖

- Python 3.13+
- Node.js 18+
- **ChromaDB** (默认使用本地持久化存储)
- **ffmpeg** (系统安装，用于音频处理及正态化)

