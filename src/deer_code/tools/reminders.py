"""为 Agent 生成“流程提醒”。

目前主要用于提醒：如果还有未完成的 todos，在给用户最终答复前要先把 todo 列表更新/收尾。

这些提醒会被拼接到各个工具的返回文本尾部，等同于一种“软约束”，帮助模型保持良好工作流。
"""

from langchain.tools import ToolRuntime

from deer_code.tools.todo.types import TodoStatus


def generate_reminders(runtime: ToolRuntime):
    # 从运行时 state 中取出 todos（由 todo_write 工具写回）。
    todos = runtime.state.get("todos")
    unfinished_todos = []
    if todos is not None:
        for todo in todos:
            if (
                todo.status != TodoStatus.completed
                and todo.status != TodoStatus.cancelled
            ):
                unfinished_todos.append(todo)

    reminders = []
    if len(unfinished_todos) > 0:
        # 这里使用英文提醒是为了与默认系统提示词保持一致（更利于模型遵循）。
        reminders.append(
            f"- {len(unfinished_todos)} todo{' is' if len(unfinished_todos) == 1 else 's are'} not completed. Before you present the final result to the user, **make sure** all the todos are completed."
        )
        reminders.append(
            "- Immediately update the TODO list using the `todo_write` tool."
        )
    """
    输出示例：
    IMPORTANT:
    - 3 todos are not completed. Before you present the final result to the user, **make sure** all the todos are completed.
    - Immediately update the TODO list using the `todo_write` tool.
    """
    return "\n\nIMPORTANT:\n" + "\n".join(reminders) if len(reminders) > 0 else ""
