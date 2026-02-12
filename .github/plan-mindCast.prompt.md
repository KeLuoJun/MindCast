## Plan: MindCast MVP — Multi-Agent AI Podcast Generator

### TL;DR

构建一个多智能体AI播客系统的MVP版本。每日自动从Tavily获取AI资讯，由主持人Agent挑选话题并深度搜索，联合3位固定MBTI人格嘉宾Agent生成约5分钟的播客对话文本（含语音标注），再通过MiniMax speech-2.8-hd合成语音并拼接为完整音频。后端使用FastAPI，前端Vue.js，LLM通过OpenAI兼容接口可配置切换（如DeepSeek）。架构预留RAG知识库、16人格动态选择、WebSocket流式TTS的扩展点。

---

### 项目目录结构

```
MindCast/
├── main.py                     # FastAPI 入口
├── pyproject.toml
├── .env                        # API Keys (TAVILY, LLM, MINIMAX)
├── backend/
│   ├── __init__.py
│   ├── config.py               # 配置管理 (Pydantic Settings)
│   ├── models.py               # 数据模型 (Episode, Dialogue, Agent等)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI路由
│   │   └── schemas.py          # API请求/响应Schema
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAgent (LLM调用封装)
│   │   ├── host.py             # HostAgent (主持人)
│   │   ├── guest.py            # GuestAgent (嘉宾)
│   │   ├── personas.py         # 16个MBTI人格定义(MVP用3个)
│   │   └── orchestrator.py     # 播客编排器 (流程控制)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── news_service.py     # Tavily新闻获取
│   │   ├── tts_service.py      # MiniMax TTS合成
│   │   ├── audio_service.py    # 音频拼接 (pydub)
│   │   └── llm_service.py      # OpenAI兼容LLM客户端
│   └── knowledge/              # 预留RAG扩展
│       ├── __init__.py
│       └── base.py             # 知识库接口定义(占位)
├── frontend/                   # Vue.js 前端
│   ├── package.json
│   ├── src/
│   │   ├── App.vue
│   │   ├── views/
│   │   │   ├── Home.vue        # 播客列表
│   │   │   └── Episode.vue     # 单期详情+播放
│   │   └── components/
│   │       ├── PodcastPlayer.vue
│   │       └── GeneratePanel.vue
│   └── ...
├── output/                     # 生成的音频和文本
│   └── episodes/
└── tests/
    ├── test_tavily.py
    ├── test_tts.py
    └── test_agents.py
```

---

### Steps

#### Step 1: 项目基础设施

1. 更新 pyproject.toml，添加依赖：`fastapi`, `uvicorn`, `httpx`, `openai`, `tavily-python`, `pydub`, `python-dotenv`, `pydantic-settings`
2. 创建 `.env` 模板文件，包含 `TAVILY_API_KEY`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `MINIMAX_API_KEY`
3. 创建 `backend/config.py`，用 Pydantic Settings 管理所有配置项，支持 `.env` 自动加载。关键配置包括：
   - LLM相关：`base_url`, `api_key`, `model`（默认指向DeepSeek）
   - MiniMax相关：`api_key`, `tts_model`（默认 `speech-2.8-hd`）
   - Tavily相关：`api_key`
   - 播客参数：`max_guests`(3), `episode_duration_minutes`(5), `output_dir`

#### Step 2: LLM 服务层

创建 `backend/services/llm_service.py`：
- 封装 `openai.AsyncOpenAI` 客户端，从 `config` 读取 `base_url`/`api_key`/`model`
- 提供 `async def chat(messages: list[dict], temperature: float, max_tokens: int) -> str` 方法
- 提供 `async def chat_stream(messages: list[dict]) -> AsyncGenerator` 流式方法（预留）
- 统一错误处理和重试逻辑

#### Step 3: Agent 系统

**3a. 基础Agent** — 创建 `backend/agents/base.py`：
- `BaseAgent` 类：持有 `name`, `system_prompt`, `llm_service` 引用
- `async def think(user_message, conversation_history) -> str` — 调用LLM生成回复
- `conversation_history: list[dict]` — 维护对话上下文

**3b. 人格定义** — 创建 `backend/agents/personas.py`：
- 定义 `PersonaConfig` 数据类：`name`, `gender`, `age`, `mbti`, `personality`, `occupation`, `speaking_style`, `voice_id`(MiniMax音色), `background`(经历)
- **MVP固定4个角色**（1主持+3嘉宾）：

| 角色 | 名字 | MBTI | 性别 | 年龄 | 职业 | 音色 |
|------|------|------|------|------|------|------|
| 主持人 | 林晨曦 | ENFJ | 女 | 32 | 科技媒体主编 | 待调试选定 |
| 嘉宾1 | 赵明远 | INTJ | 男 | 38 | AI算法工程师 | 待调试选定 |
| 嘉宾2 | 苏婉清 | ENTP | 女 | 29 | AI创业者/产品经理 | 待调试选定 |
| 嘉宾3 | 陈志恒 | INFP | 男 | 45 | AI伦理研究员 | 待调试选定 |

- 预留全部16个MBTI角色的定义位置，MVP仅使用上述4个
- 每个角色的 `system_prompt` 需融合MBTI特征、职业背景、说话风格：
  - INTJ：逻辑严密、直接、喜欢用数据说话
  - ENTP：活跃、喜欢辩论、善于类比、发散思维
  - INFP：关注人文、伦理、社会影响，温和但有坚定立场
  - ENFJ：善于引导话题、总结观点、调动气氛

**3c. 主持人Agent** — 创建 `backend/agents/host.py`：
- 继承 `BaseAgent`
- `async def select_topic(news_list: list[dict]) -> dict` — 从多条AI资讯中挑选1个方向，返回选定话题及理由
- `async def plan_episode(topic: dict, detailed_info: list[dict]) -> EpisodePlan` — 根据深度信息规划节目大纲（开场、讨论点、总结等）
- `async def generate_line(context: ConversationContext) -> DialogueLine` — 生成主持人的一句台词（含语音标注）

**3d. 嘉宾Agent** — 创建 `backend/agents/guest.py`：
- 继承 `BaseAgent`
- `async def generate_line(context: ConversationContext) -> DialogueLine` — 根据当前讨论上下文生成嘉宾发言
- 发言需体现该角色的MBTI性格、职业视角、独立见解

**3e. 播客编排器** — 创建 `backend/agents/orchestrator.py`（**核心模块**）：

整体流程方法 `async def generate_episode() -> Episode`：
1. **资讯获取阶段**：调用 `news_service` 获取当日AI资讯（~10条）
2. **话题选定阶段**：调用 `host.select_topic()` 挑选1个方向
3. **深度搜索阶段**：对选定话题调用至多5次 `news_service.search_detail()`，用不同关键词/角度获取深度信息
4. **节目策划阶段**：调用 `host.plan_episode()` 生成节目大纲
5. **对话生成阶段**：按大纲逐轮生成对话，交替control主持人与嘉宾发言
   - 维护一个共享的 `conversation_context`（所有角色可见的对话历史）
   - 主持人负责引导、提问、转场、总结
   - 嘉宾按轮次发言（不必每轮每人都说，主持人决定下一个发言者）
   - 生成的每条 `DialogueLine` 包含：`speaker`, `text`, `emotion`, `pause_before`, `pause_after`
   - 控制总字数在约1500-2000字（对应~5分钟播客）
6. **语音合成阶段**：逐条台词调用 `tts_service` 合成音频
7. **音频拼接阶段**：调用 `audio_service` 将所有片段拼接为完整MP3

#### Step 4: 新闻获取服务

创建 `backend/services/news_service.py`：
- `async def get_daily_ai_news(max_results=10) -> list[NewsItem]` — 调用 Tavily `search(query="AI人工智能最新资讯", topic="news", time_range="day", max_results=10, include_answer=True)`
- `async def search_detail(query: str, search_depth="advanced") -> DetailedInfo` — 对特定话题进行深度搜索，返回详细内容
- `NewsItem` 数据模型包含：`title`, `url`, `content`, `published_date`, `score`

#### Step 5: 对话文本生成与语音标注

`DialogueLine` 数据模型设计：
```
speaker: str           # 发言人名
text: str              # 原始文本（用于展示）
ssml_text: str         # 带语音标注的文本（用于TTS）
emotion: str           # 情感标签 (用于TTS voice_setting)
voice_id: str          # 该发言人的音色ID
```

文本生成时，LLM的prompt需指导模型：
- 在文本中自然地插入 MiniMax 的停顿标签 `<#1.0#>` 用于思考停顿、转折等
- 在文本中插入情感标签如 `(laughs)`, `(sighs)` 等（speech-2.8-hd 支持）
- 通过节目大纲控制节奏：开场寒暄→话题引入→多角度讨论→总结展望
- 语言风格：主体中文，AI术语和专有名词可用英文（如 "Transformer"、"AGI"）

#### Step 6: TTS 语音合成服务

创建 `backend/services/tts_service.py`：
- `async def synthesize(text: str, voice_id: str, emotion: str = None) -> bytes`
- 调用 MiniMax HTTP API `POST https://api.minimaxi.com/v1/t2a_v2`
- 请求体：
  - `model`: `speech-2.8-hd`
  - `text`: 带标注的文本
  - `voice_setting`: `{voice_id, speed: 1.0, vol: 1.0, emotion}`
  - `audio_setting`: `{sample_rate: 32000, format: "mp3", channel: 1}`
  - `language_boost`: `Chinese`
  - `output_format`: `hex`（解码 hex 得到 bytes）
- 每条台词单独合成（不同发言人不同音色），text上限10000字符
- 错误重试 + 速率限制处理

#### Step 7: 音频拼接服务

创建 `backend/services/audio_service.py`：
- 依赖 `pydub`（需系统安装 `ffmpeg`）
- `async def stitch_episode(audio_segments: list[AudioSegment], output_path: str) -> str`
- 流程：
  1. 将每段hex bytes → MP3 bytes → `AudioSegment`
  2. 音量标准化到统一 dBFS
  3. 各段之间插入合适的静音间隔（200-500ms，根据 `DialogueLine.pause_after` 决定）
  4. 可选：添加开场/结尾背景音乐（MVP可先不加）
  5. 导出为最终 MP3 文件到 `output/episodes/`

#### Step 8: 数据模型

创建 `backend/models.py`：
- `NewsItem`: 新闻条目
- `PersonaConfig`: 人格配置
- `DialogueLine`: 单条对话（含语音标注）
- `EpisodePlan`: 节目大纲
- `Episode`: 完整一期播客（元数据 + 对话列表 + 音频路径）
- 使用 Pydantic BaseModel，MVP阶段以JSON文件持久化到 `output/episodes/`，预留后续数据库迁移

#### Step 9: FastAPI 后端

更新 main.py，创建 `backend/api/routes.py`：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/generate` | POST | 触发生成新一期播客 |
| `/api/episodes` | GET | 获取已生成的播客列表 |
| `/api/episodes/{id}` | GET | 获取某期详情（文本+音频URL） |
| `/api/episodes/{id}/audio` | GET | 返回音频文件流 |
| `/api/status/{task_id}` | GET (SSE) | 生成进度的实时推送 |

- 播客生成为异步任务（`BackgroundTasks` 或简单的 `asyncio.create_task`）
- SSE (Server-Sent Events) 推送生成进度：资讯获取中 → 话题选定 → 深度搜索 → 脚本生成 → 语音合成(x/n) → 音频拼接 → 完成
- 静态文件服务挂载 `output/episodes/` 目录

#### Step 10: Vue.js 前端

创建 `frontend/` Vue 3 项目（Vite构建）：

**首页 (Home.vue)**：
- 播客列表，展示：日期、话题标题、时长、嘉宾
- "生成新一期"按钮

**生成面板 (GeneratePanel.vue)**：
- 点击生成后展示实时进度（通过SSE连接）
- 各阶段状态指示（获取资讯✓ → 选题✓ → 深度搜索... → 生成文本... → 合成语音...）

**播放页 (Episode.vue)**：
- 音频播放器组件
- 对话文本展示（带发言人头像/名字/高亮当前播放段）
- 话题摘要、参考来源链接

#### Step 11: 知识库扩展预留

创建 `backend/knowledge/base.py`：
- 定义 `KnowledgeBase` 抽象接口：`async def store(doc)`, `async def query(text, top_k) -> list`
- MVP实现一个 `DummyKnowledgeBase`（空操作，直接返回空列表）
- 后续接入 ChromaDB 时只需实现该接口

---

### Verification

1. **单元测试**：`tests/test_tavily.py` 验证新闻获取 → `tests/test_tts.py` 验证单句TTS合成 → `tests/test_agents.py` 验证Agent对话生成
2. **集成测试**：运行一次完整的 `orchestrator.generate_episode()`，检查：
   - 是否成功获取到当日AI资讯
   - 主持人是否合理选题
   - 对话文本是否自然、有深度、角色风格区分明显
   - 总字数是否在1500-2000字范围
   - 每条台词的TTS是否成功合成
   - 最终拼接的MP3是否可正常播放、时长约5分钟
3. **前端验证**：启动FastAPI + Vue dev server，验证播客生成→列表展示→音频播放完整链路
4. **音色调试**：调用 MiniMax `/v1/get_voice` 获取可用音色列表，为4个角色分别选定合适的中文音色

### Decisions

- **LLM选择**：采用通用OpenAI兼容接口，通过 `.env` 配置 `base_url` 和 `model`，可切换DeepSeek/其他模型，无供应商锁定
- **TTS模型**：选用 `speech-2.8-hd`（最高质量），通过内联情感标签 `(laughs)`/`(sighs)` 和停顿标签 `<#1.0#>` 控制语音表现力，而非emotion参数
- **Agent架构**：不引入多智能体框架（如CrewAI/AutoGen），直接基于OpenAI SDK封装，每个Agent本质是一组 system_prompt + 对话历史。简单可控，无额外依赖
- **对话生成策略**：非一次性生成全部文本，而是逐轮生成——主持人先说→指定下一位发言者→嘉宾回应→主持人接话/追问→循环。这样每个Agent都能看到前文并做出有针对性的回应，对话更自然
- **MVP暂缓**：ChromaDB RAG、16人格动态选择、WebSocket流式TTS、背景音乐，均通过接口/目录预留扩展点
- **持久化**：MVP用JSON文件+音频文件存储，预留后续SQLite/PostgreSQL迁移路径

---

### 推荐的开发顺序（4个迭代阶段）

**Phase 1 — 基础管道** (Step 1-2-4)：项目骨架 + 配置 + LLM调通 + Tavily资讯获取验证

**Phase 2 — Agent对话引擎** (Step 3-5-8)：Agent系统 + 人格定义 + 编排器 + 完整文本生成管道

**Phase 3 — 语音合成** (Step 6-7)：TTS集成 + 音频拼接 + 端到端生成完整播客

**Phase 4 — Web界面** (Step 9-10-11)：FastAPI API + Vue前端 + 知识库预留
