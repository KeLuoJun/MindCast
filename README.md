# MindCast · 智想电波

> 多智能体 AI 播客生成器 — 每日 AI 资讯深度解读

MindCast 是一个多智能体系统，每日自动从 Tavily 获取最新 AI 资讯，由主持人 Agent 挑选话题，联合 3 位不同 MBTI 人格的嘉宾 Agent 生成约 5 分钟的播客对话文本，再通过 MiniMax `speech-2.8-hd` 合成语音并拼接为完整音频。

## 架构

- **后端**：FastAPI + OpenAI-compatible LLM + Tavily + MiniMax TTS
- **前端**：Vue 3 + Vite
- **Agent 系统**：基于 LangGraph 的状态图编排（news → topic → research → planning → dialogue → tts → audio）
- **可观测性**：每次生成会落地完整结构化日志到 `output/episodes/logs/{episode_id}.jsonl`

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
# 编辑 .env 填入你的 API Keys
```

### 2. 安装后端依赖

```bash
pip install -e .
```

### 3. 启动后端

```bash
python main.py
# 或者：uvicorn main:app --reload
```

### 4. 安装和启动前端

```bash
cd frontend
npm install
npm run dev
```

如需自定义后端地址（例如远程后端），可在启动前设置：

```bash
# Windows PowerShell
$env:VITE_API_TARGET="http://127.0.0.1:8000"
npm run dev
```

### 5. 使用

- 访问 `http://localhost:5173` 打开前端
- 点击 "生成新一期播客" 按钮
- 等待生成完成后即可收听

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/generate` | POST | 触发生成新一期播客 |
| `/api/episodes` | GET | 获取已生成的播客列表 |
| `/api/episodes/{id}` | GET | 获取某期详情 |
| `/api/episodes/{id}/audio` | GET | 返回音频文件流 |
| `/api/status/{task_id}` | GET (SSE) | 生成进度实时推送 |

## 前置依赖

- Python 3.13+
- Node.js 18+
- ffmpeg (系统安装，用于音频处理)
