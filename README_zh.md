# 🦌 deer-code

一个极简但强大的 AI 编程智能体项目，帮助开发者学习并构建智能编码助手。项目使用 Python 构建，并提供类似 VSCode 的 TUI 界面；`deer-code` 展示了如何创建能够进行推理、规划与行动（对代码动手）的 AI Agent。

<img width="2764" height="1988" alt="Screenshot" src="https://github.com/user-attachments/assets/3a86b15f-d616-4b56-80c9-63fccb4d8f28" />

**由** [🦌 The DeerFlow Team](https://github.com/bytedance/deer-flow) **为你带来**。

*灵感来自 Anthropic 的 Claude Code。*

## 🚀 快速开始

DeerCode 使用 Python 编写，旨在便于安装与使用。按以下步骤开始：

### 前置条件

- [Python](https://www.python.org/downloads/) 3.12 或更高版本
- [uv](https://docs.astral.sh/uv/)（推荐用于依赖管理）
- [langgraph-cli](https://docs.langchain.com/langsmith/cli)（用于开发与调试）

### 安装

1. **克隆仓库：**
   ```bash
   git clone https://github.com/bytedance/deer-flow.git
   cd deer-flow
   ```

2. **安装依赖：**
   ```bash
   make install
   ```

### 配置

1. **复制配置模板：**
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **编辑 `config.yaml`，填入你的配置：**

```yaml
models:
  chat_model:
    model: 'gpt-5-2025-08-07'
    api_base: 'https://api.openai.com/v1'
    api_key: $OPENAI_API_KEY
    temperature: 0
    max_tokens: 8192
    extra_body:
      reasoning_effort: minimal # `minimal`, `low`, `medium` or `high`
  # 你也可以取消注释下面这一段来使用豆包模型：
  #
  # chat_model:
  #   type: doubao
  #   model: 'doubao-seed-1-6-250615'
  #   api_base: 'https://ark.cn-beijing.volces.com/api/v3'
  #   api_key: $ARK_API_KEY
  #   temperature: 0
  #   max_tokens: 8192
  #   extra_body:
  #     thinking:
  #       type: auto
tools:
  mcp_servers:
    context7:
      transport: 'streamable_http'
      url: 'https://mcp.context7.com/mcp'
    # your_mcp_server:
    #   ...
```

### 运行应用

**启动 deer-code：**
```bash
uv run -m deer_code.main "/path/to/your/developing/project"
```

**开发模式（使用 LangGraph CLI）：**

首先，在 `langgraph.json` 文件中修改 `env.PROJECT_ROOT`。

然后运行：
```bash
make dev
```

接着打开浏览器并访问 `https://agentchat.vercel.app/?apiUrl=http://localhost:2024&assistantId=coding_agent` 与 Agent 对话。

## 🌟 功能特性

- [x] **对新手友好**：为学习而设计的简洁项目结构
- [x] **类 VSCode 的 CUI**：直观的终端界面
- [x] **OpenAI 兼容**：支持任意 OpenAI 兼容 API
- [x] **ReAct 框架**：具备推理、规划与行动能力
- [x] **多轮对话**：跨轮次保持上下文
- [x] **任务规划**：内置 todo 系统用于项目管理
- [x] **代码生成**：AI 驱动的代码创建与编辑
- [x] **代码搜索**：更智能的代码定位与搜索
- [x] **Bash 执行**：支持 Bash 命令执行
- [x] **MCP 集成**：接入你自己的 MCP 工具以增强 Agent 能力

## 🤝 参与贡献

欢迎贡献！详情请参阅我们的 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

本项目为开源项目，使用 [MIT License](./LICENSE)。

## 🙏 致谢

- 灵感来自 [Anthropic's Claude Code](https://github.com/anthropics/claude-code)
- TUI 界面基于 [Textual](https://github.com/Textualize/textual)
- Agent 编排基于 [LangGraph](https://github.com/langchain-ai/langgraph)
