"""`ls` tool: list files and directories with optional match/ignore filters.

`ls` 工具：列出目录下的文件与子目录（带 match/ignore 过滤）。

Design goals:
- Enforce absolute paths to avoid ambiguity and accidental operations.
- Sort directories before files, both alphabetically, for better readability.
- Apply a default set of ignore patterns (e.g. node_modules, .git) to reduce noise.
- Append reminders (e.g. unfinished todos) at the end of the output.

实现目标：
- 强制绝对路径，降低误操作与歧义；
- 先按“目录优先、名字排序”输出，提升可读性；
- 默认附加一组常见 ignore 规则，避免 node_modules、.git 等干扰；
- 在返回末尾追加 reminders（例如 todo 未完成提醒）。
"""

import fnmatch
from pathlib import Path
from typing import Optional

from langchain.tools import ToolRuntime, tool

from deer_code.tools.reminders import generate_reminders

from .ignore import DEFAULT_IGNORE_PATTERNS


@tool("ls", parse_docstring=True)
def ls_tool(
    runtime: ToolRuntime,
    path: str,
    match: Optional[list[str]] = None,
    ignore: Optional[list[str]] = None,
):
    """Lists files and directories in a given path. Optionally provide an array of glob patterns to match and ignore.

    在指定路径下列出文件和子目录，可选提供 glob 模式进行匹配或忽略。

    Args:
        path: The absolute path to list files and directories from. Relative paths are **not** allowed.
              要列出内容的绝对路径，不允许相对路径。
        match: An optional array of glob patterns to match.
               可选的匹配模式列表（仅保留名称匹配这些模式的条目）。
        ignore: An optional array of glob patterns to ignore.
                可选的忽略模式列表（会与默认的忽略规则合并）。
    """
    _path = Path(path)
    if not _path.is_absolute():
        return f"Error: the path {path} is not an absolute path. Please provide an absolute path."
    if not _path.exists():
        return f"Error: the path {path} does not exist. Please provide a valid path."

    if not _path.is_dir():
        return f"Error: the path {path} is not a directory. Please provide a valid directory path."

    # 获取目录下的所有项
    try:
        items = list(_path.iterdir())
    except PermissionError:
        return f"Error: permission denied to access the path {path}."

    # 排序：目录优先，文件其次，按字母顺序
    items.sort(key=lambda x: (x.is_file(), x.name.lower()))

    # 应用匹配模式（如果提供）
    if match:
        filtered_items = []
        for item in items:
            for pattern in match:
                # match 只针对“名称”匹配（而非完整路径），便于用户写简单模式如 *.py
                if fnmatch.fnmatch(item.name, pattern):
                    filtered_items.append(item)
                    break
        items = filtered_items

    # 合并 ignore：用户传入 + 默认忽略规则
    ignore = (ignore or []) + DEFAULT_IGNORE_PATTERNS
    filtered_items = []
    for item in items:
        should_ignore = False
        for pattern in ignore:
            if fnmatch.fnmatch(item.name, pattern):
                should_ignore = True
                break
        if not should_ignore:
            filtered_items.append(item)
    items = filtered_items

    reminders = generate_reminders(runtime)

    # 格式化输出
    if not items:
        return f"No items found in {path}.{reminders}"

    result_lines = []
    for item in items:
        if item.is_dir():
            result_lines.append(item.name + "/")
        else:
            result_lines.append(item.name)

    return (
        f"Here's the result in {path}: \n```\n"
        + "\n".join(result_lines)
        + f"\n```{reminders}"
    )


if __name__ == "__main__":
    print(
        ls_tool.invoke(
            {
                "path": "/Users/henry/Desktop/next-js-demo",
                "ignore": ["*.js*"],
            }
        )
    )
