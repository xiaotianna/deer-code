import os

from langchain.agents import create_agent
from langchain.tools import BaseTool
from langgraph.checkpoint.base import RunnableConfig

from deer_code.models import init_chat_model
from deer_code.project import project
from deer_code.prompts import apply_prompt_template
from deer_code.tools import (
    bash_tool,
    grep_tool,
    ls_tool,
    text_editor_tool,
    todo_write_tool,
    tree_tool,
)

from .state import CodingAgentState


def create_coding_agent(plugin_tools: list[BaseTool] = [], **kwargs):
    """Create a coding agent.

    Args:
        plugin_tools: 额外注入到 Agent 的工具（会追加在内置工具后面）。
        **kwargs: 透传给 `create_agent` 的额外参数（例如 debug 开关等）。

    Returns:
        构建好的 coding agent（LangChain/LangGraph 运行时可执行对象）。
    """
    # 这里把模型、工具列表、系统提示词与状态结构组装成一个 Agent。
    # 运行时 Agent 会基于 system_prompt + 状态（CodingAgentState）进行多轮推理，
    # 并在需要时调用 tools 列表中的工具来完成任务。
    return create_agent(
        # 初始化对话模型（具体实现由 `deer_code.models.init_chat_model` 决定，
        # 通常会从配置文件/环境变量读取模型与 API 参数）。
        model=init_chat_model(),
        # 工具列表：内置工具 + 可选的 plugin_tools（用于扩展能力）。
        # 注意：工具顺序有时会影响模型在选择工具时的偏好。
        tools=[
            bash_tool,
            grep_tool,
            ls_tool,
            text_editor_tool,
            todo_write_tool,
            tree_tool,
            *plugin_tools,
        ],
        # 系统提示词：从 prompts/templates 中加载 `coding_agent` 模板，
        # 并把当前项目根目录注入进去，便于 Agent 知道“在哪个项目里工作”。
        system_prompt=apply_prompt_template(
            "coding_agent", PROJECT_ROOT=project.root_dir
        ),
        # 状态结构：定义 Agent 在多轮过程中可读写的状态字段。
        state_schema=CodingAgentState,
        # Agent 名称：用于调试/可视化/追踪（例如 LangGraph/LangSmith）。
        name="coding_agent",
        **kwargs,
    )


def create_coding_agent_for_debug(config: RunnableConfig):
    # Debug 场景下允许通过环境变量覆盖项目根目录，避免必须从当前 cwd 启动。
    # `config` 是 LangGraph 在运行时注入的配置对象（这里未使用，但保留接口以对齐调用约定）。
    project.root_dir = os.getenv("PROJECT_ROOT", os.getcwd())
    # 透传 debug=True，让下游 `create_agent`/模型层开启更友好的调试行为（视实现而定）。
    return create_coding_agent(debug=True)
