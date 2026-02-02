"""`bash` 工具：在可复用的 shell 会话中执行命令。

为什么要“keep-alive”：
- 多条命令之间可以共享工作目录与部分 shell 状态；
- 对于需要连续执行的开发任务（安装依赖、跑测试、起服务）更自然。

注意：
- 文件系统的只读操作优先用 `ls` / `grep` / `tree` 工具，避免 bash 输出不可控；
- 如需创建/编辑文件，优先用 `text_editor` 工具，便于审计与约束。
"""

from typing import Optional

from langchain.tools import ToolRuntime, tool

from deer_code.project import project
from deer_code.tools.reminders import generate_reminders

from .bash_terminal import BashTerminal

keep_alive_terminal: BashTerminal | None = None


@tool("bash", parse_docstring=True)
def bash_tool(runtime: ToolRuntime, command: str, reset_cwd: Optional[bool] = False):
    """Execute a standard bash command in a keep-alive shell, and return the output if successful or error message if failed.
    在常驻 shell 中执行 bash 命令，成功则返回输出，失败则返回错误信息。

    Use this tool to perform:
    可用于执行以下操作：
    - Create directories
    - 创建目录
    - Install dependencies
    - 安装依赖
    - Start development server
    - 启动开发服务
    - Run tests and linting
    - 运行测试与代码检查
    - Git operations
    - Git 相关操作

    Never use this tool to perform any harmful or dangerous operations.
    切勿用此工具执行任何有害或危险操作。

    - Use `ls`, `grep` and `tree` tools for file system operations instead of this tool.
    - 文件系统操作请优先使用 `ls`、`grep`、`tree` 等工具，而非本工具。
    - Use `text_editor` tool with `create` command to create new files.
    - 创建新文件请使用 `text_editor` 的 `create` 命令。

    Args:
        command: The command to execute.
        command: 要执行的命令。
        reset_cwd: Whether to reset the current working directory to the project root directory.
        reset_cwd: 是否将当前工作目录重置为项目根目录。
    """
    global keep_alive_terminal
    if keep_alive_terminal is None:
        # First call: initialize terminal with cwd set to project root.
        # 首次调用时初始化终端，并把 cwd 设为项目根目录。
        keep_alive_terminal = BashTerminal(project.root_dir)
    elif reset_cwd:
        # When reset_cwd=True, recreate session to return to project root and clear shell state.
        # reset_cwd=True 时重建会话，用于回到项目根目录并清掉潜在的 shell 状态影响。
        keep_alive_terminal.close()
        keep_alive_terminal = BashTerminal(project.root_dir)

    reminders = generate_reminders(runtime)
    return f"```\n{keep_alive_terminal.execute(command)}\n```{reminders}"
