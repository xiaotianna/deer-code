"""deer_code.tools

这里集中导出 Agent 可用的“工具（tools）”。

在 LangChain/LangGraph 体系里，tool 通常是一个可被模型调用的函数（带有名称、参数 schema
与文档说明），用于让 Agent 执行“读写文件/搜索/跑命令/维护 todo”等具有副作用或需要系统能力的操作。
"""

from .edit import text_editor_tool
from .fs import grep_tool, ls_tool, tree_tool
from .mcp import load_mcp_tools
from .terminal.tool import bash_tool
from .todo import todo_write_tool

__all__ = [
    "bash_tool",
    "grep_tool",
    "load_mcp_tools",
    "ls_tool",
    "text_editor_tool",
    "todo_write_tool",
    "tree_tool",
]
