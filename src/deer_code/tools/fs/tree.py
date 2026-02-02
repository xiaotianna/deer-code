"""`tree` tool: display directory structure in a tree-like view.

`tree` 工具：以树形结构展示目录内容（类似系统的 tree 命令）。

Implementation notes:
- Recursively traverse directories, listing directories before files.
- Support max_depth to limit traversal depth and avoid huge outputs.
- Use DEFAULT_IGNORE_PATTERNS to skip common noisy paths.
- Append reminders (e.g. unfinished todos) at the end of the output.

实现方式：
- 递归遍历目录，优先展示目录再展示文件；
- 支持 max_depth 限制遍历深度，避免输出过大；
- 结合 DEFAULT_IGNORE_PATTERNS 过滤常见噪音目录/文件；
- 输出末尾追加 reminders（例如 todo 未完成提醒）。
"""

import fnmatch
from pathlib import Path
from typing import Optional

from langchain.tools import ToolRuntime, tool

from deer_code.tools.reminders import generate_reminders

from .ignore import DEFAULT_IGNORE_PATTERNS


def should_ignore(path: Path, ignore_patterns: list[str]) -> bool:
    """Return True if a path should be ignored according to ignore_patterns.

    根据 ignore_patterns 判断某个 path 是否应被跳过。
    """
    path_str = str(path)
    name = path.name

    for pattern in ignore_patterns:
        # 移除 /** 或 /* 后缀用于匹配，例如："dist/**",
        clean_pattern = pattern.rstrip("/**").rstrip("/*")

        # 匹配名称或完整路径
        if fnmatch.fnmatch(name, clean_pattern) or fnmatch.fnmatch(path_str, pattern):
            return True

    return False


def generate_tree(
    directory: Path,
    prefix: str = "",
    max_depth: Optional[int] = None,
    current_depth: int = 0,
    ignore_patterns: list[str] = None,
) -> list[str]:
    """Recursively generate the tree lines for a directory.

    递归生成树形结构的每一行文本（不包含最顶层根路径那一行）。
    """
    if ignore_patterns is None:
        ignore_patterns = []

    lines = []

    # 检查深度限制
    if max_depth is not None and current_depth >= max_depth:
        return lines

    try:
        # 获取所有条目并排序（目录优先，然后是文件）
        entries = sorted(
            directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())
        )

        # 过滤掉忽略的条目
        entries = [e for e in entries if not should_ignore(e, ignore_patterns)]

        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1

            # 确定树字符
            if is_last:
                connector = "└── "
                extension = "    "
            else:
                connector = "├── "
                extension = "│   "

            # 添加条目
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                # 递归进入子目录
                if max_depth is None or current_depth + 1 < max_depth:
                    sub_lines = generate_tree(
                        entry,
                        prefix + extension,
                        max_depth,
                        current_depth + 1,
                        ignore_patterns,
                    )
                    lines.extend(sub_lines)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    except PermissionError:
        # 遇到无权限目录时不中断整体输出，改为在树中提示该分支不可访问。
        lines.append(f"{prefix}[Permission Denied]")

    """
    返回的是 list[str]，即树形结构的每一行文本（不含根路径那一行）
    generate_tree(Path("/Users/foo/project"), max_depth=3) 的返回值为
    [
        "├── src/",
        "│   ├── main.py",
        "│   └── utils.py",
        "├── README.md",
        "└── config.yaml",
    ]
    """
    return lines


@tool("tree", parse_docstring=True)
def tree_tool(
    runtime: ToolRuntime,
    path: Optional[str] = None,
    max_depth: Optional[int] = 3,
) -> str:
    """Display directory structure in a tree format, similar to the 'tree' command.
    以树形结构展示目录，类似系统的 tree 命令。

    Shows files and directories in a hierarchical tree structure.
    以层级树的形式展示文件和目录。

    Automatically excludes common ignore patterns (version control, dependencies, build artifacts, etc.).
    自动排除常见忽略项（版本控制、依赖、构建产物等）。

    Args:
        path: Directory path to display. Defaults to current working directory if not specified.
              要展示的目录路径；未指定时默认为当前工作目录。
        max_depth: Maximum depth to traverse. The max_depth should be less than or equal to 3. Defaults to 3.
                  最大遍历深度，建议不超过 3；默认为 3。

    Returns:
        A tree-structured view of the directory as a string.
        目录的树形结构字符串。
    """
    # 设置搜索路径
    search_path = Path(path) if path else Path(".")

    try:
        # 验证路径
        if not search_path.exists():
            return f"Error: Path '{search_path}' does not exist."

        if not search_path.is_dir():
            return f"Error: Path '{search_path}' is not a directory."

        # 生成树
        lines = [str(search_path.resolve()) + "/"]
        tree_lines = generate_tree(
            search_path,
            max_depth=max_depth,
            ignore_patterns=DEFAULT_IGNORE_PATTERNS,
        )
        lines.extend(tree_lines)

        # 统计目录和文件
        dir_count = sum(1 for line in tree_lines if line.rstrip().endswith("/"))
        file_count = len(tree_lines) - dir_count

        # 添加总结
        lines.append("")
        lines.append(f"{dir_count} directories, {file_count} files")

        output = "\n".join(lines)

        # 格式化结果
        return f"Here's the result in {search_path}:\n\n```\n{output}\n```{generate_reminders(runtime)}"

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print(tree_tool.invoke({"path": "/Users/lantianyu/Desktop/llm-ai-chat"}))
