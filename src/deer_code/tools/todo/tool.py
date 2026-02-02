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
    """Update the entire TODO list with the latest items.

    Args:
        todos: A list of TodoItem objects.
    """
    # Do nothing, but save the latest to-dos to the state.
    # 这里通过返回 Command(update=...) 的方式，把 todos 和一条 ToolMessage 写回 state。

    unfinished_todos = []
    for todo in todos:
        if todo.status != TodoStatus.completed and todo.status != TodoStatus.cancelled:
            unfinished_todos.append(todo)

    message = f"Successfully updated the TODO list with {len(todos)} items."
    if len(unfinished_todos) > 0:
        # 这条提示信息会作为 ToolMessage 写入 messages，便于 UI/日志显示工具调用结果。
        message += f" {len(unfinished_todos)} todo{' is' if len(unfinished_todos) == 1 else 's are'} not completed."
    else:
        message += " All todos are completed."

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
