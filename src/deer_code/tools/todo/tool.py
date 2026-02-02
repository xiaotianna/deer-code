"""`todo_write` 工具：把最新的 todo 列表写回 Agent state。

在这个项目里，todo 更像是一种“显式任务跟踪状态”：
- Agent 通过调用 todo_write 来更新任务清单；
- 其他工具会读取 state 里的 todos，并在必要时生成提醒（reminders）；
- UI 层也可以展示 todos，帮助用户理解 Agent 的执行进度。
"""

from typing import Annotated

from langchain.messages import ToolMessage
from langchain.tools import InjectedToolCallId, tool
from langgraph.graph.state import Command

from .types import TodoItem, TodoStatus


@tool("todo_write", parse_docstring=True)
def todo_write_tool(
    todos: list[TodoItem], tool_call_id: Annotated[str, InjectedToolCallId]
):
    """用最新条目覆盖并更新整个 TODO 列表。

    参数：
        todos：TodoItem 的列表（将被写入到 Agent state 的 `todos` 字段中）。
    """
    # 该工具本身不做“业务处理”，核心职责是把最新的 todos 写回到 Agent 的 state。
    # 这里通过返回 Command(update=...) 的方式，把 `todos` 和一条 ToolMessage 写回 state，
    # 以便后续工具（例如 reminders）或 UI 能够读取并展示最新的任务进度。

    # 收集未完成的 todo（用于生成更友好的提示信息）。
    unfinished_todos = []
    for todo in todos:
        if todo.status != TodoStatus.completed and todo.status != TodoStatus.cancelled:
            unfinished_todos.append(todo)

    # 生成工具调用结果消息：写入 messages，便于 UI/日志展示。
    message = f"已成功更新 TODO 列表，共 {len(todos)} 项。"
    if len(unfinished_todos) > 0:
        # 中文不需要处理单复数：直接说明还有多少项未完成即可。
        message += f"其中 {len(unfinished_todos)} 项未完成。"
    else:
        message += "全部已完成。"

    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(
                    message,
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )
