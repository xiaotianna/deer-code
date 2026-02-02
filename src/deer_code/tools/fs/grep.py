"""`grep` tool: regex search based on ripgrep (rg).

`grep` 工具：基于 ripgrep（rg）进行正则搜索。

Why wrap it as a tool:
- Standardize on using rg from the agent side instead of shelling out to grep/rg.
- Automatically apply default ignore patterns to reduce noise and improve performance.
- Expose options like output_mode, context lines, file type filters, and multiline search.

为什么封装成工具：
- 统一在 Agent 侧使用 rg，避免用 Bash 直接跑 grep/rg（更难约束、也更难解析输出）；
- 自动附加默认 ignore 规则，减少噪音与性能开销；
- 提供 output_mode / 上下文行数 / 语言类型过滤 / 多行匹配等参数。
"""

import subprocess
from typing import Literal, Optional

from langchain.tools import ToolRuntime, tool

from deer_code.tools.reminders import generate_reminders

from .ignore import DEFAULT_IGNORE_PATTERNS

# Unix/Linux 系统中的经典文本搜索工具
@tool("grep", parse_docstring=True)
def grep_tool(
    runtime: ToolRuntime,
    pattern: str,
    path: Optional[str] = None,
    glob: Optional[str] = None,
    output_mode: Literal[
        "content", "files_with_matches", "count"
    ] = "files_with_matches",
    B: Optional[int] = None,
    A: Optional[int] = None,
    C: Optional[int] = None,
    n: Optional[bool] = None,
    i: Optional[bool] = None,
    type: Optional[str] = None,
    head_limit: Optional[int] = None,
    multiline: Optional[bool] = False,
) -> str:
    """A powerful search tool built on ripgrep for searching file contents with regex patterns.

    基于 ripgrep 的强大搜索工具，用正则在文件内容中查找匹配。

    ALWAYS use this tool for search tasks. NEVER invoke `grep` or `rg` as a Bash command.
    Supports full regex syntax, file filtering, and various output modes.

    在 Agent 中进行搜索时，应始终使用该工具，而不要在 Bash 中直接执行 `grep` 或 `rg`。
    该工具支持完整的正则语法、文件过滤以及多种输出模式。

    Args:
        pattern: The regular expression pattern to search for in file contents.
                Uses ripgrep syntax - literal braces need escaping (e.g., `interface\\{\\}` for `interface{}`).
                用于匹配文件内容的正则表达式模式（使用 ripgrep 语法，注意花括号需要转义）。
        path: File or directory to search in. Defaults to current working directory if not specified.
              搜索的文件或目录路径；未指定时默认为当前工作目录。
        glob: Glob pattern to filter files (e.g., "*.js", "*.{ts,tsx}").
              用于过滤文件的 glob 模式（如 `"*.js"`、`"*.{ts,tsx}"`）。
        output_mode: Output mode - "content" shows matching lines with optional context,
                    "files_with_matches" shows only file paths (default),
                    "count" shows match counts per file.
                     输出模式："content" 输出带上下文的匹配行；
                     "files_with_matches" 只输出包含匹配的文件路径（默认）；
                     "count" 输出每个文件的匹配次数。
        B: Number of lines to show before each match. Only works with output_mode="content".
           每个匹配前要显示的行数（仅在 output_mode="content" 时生效）。
        A: Number of lines to show after each match. Only works with output_mode="content".
           每个匹配后要显示的行数（仅在 output_mode="content" 时生效）。
        C: Number of lines to show before and after each match. Only works with output_mode="content".
           每个匹配前后要同时显示的行数（仅在 output_mode="content" 时生效）。
        n: Show line numbers in output. Only works with output_mode="content".
           是否在输出中显示行号（仅在 output_mode="content" 时生效）。
        i: Enable case insensitive search.
           是否启用大小写不敏感搜索。
        type: File type to search (e.g., "js", "py", "rust", "go", "java").
             More efficient than glob for standard file types.
             按文件类型过滤（如 "js"、"py" 等），对标准类型比 glob 更高效。
        head_limit: Limit output to first N lines/entries. Works across all output modes.
                    将输出限制在前 N 行/条记录（所有 output_mode 下均有效）。
        multiline: Enable multiline mode where patterns can span lines and . matches newlines.
                  Default is False (single-line matching only).
                   是否启用多行模式（模式可跨行，`.` 匹配换行）；默认 False，仅在单行内匹配。

    Returns:
        Search results as a string, formatted according to the output_mode.

        返回按 output_mode 格式化后的搜索结果字符串。
    """
    # Build ripgrep command
    cmd = ["rg"]

    # Add pattern
    cmd.append(pattern)

    # Add path if specified
    search_path = path if path else "."
    cmd.append(search_path)

    # Add output mode flags
    if output_mode == "files_with_matches":
        cmd.append("-l")
    elif output_mode == "count":
        cmd.append("-c")
    # content mode is default, no flag needed

    # Add context flags (only for content mode)
    if output_mode == "content":
        if C is not None:
            cmd.extend(["-C", str(C)])
        else:
            if B is not None:
                cmd.extend(["-B", str(B)])
            if A is not None:
                cmd.extend(["-A", str(A)])
        if n:
            cmd.append("-n")

    # Add case insensitive flag
    if i:
        cmd.append("-i")

    # Add file type filter
    if type:
        cmd.extend(["--type", type])

    # Add glob pattern
    if glob:
        cmd.extend(["--glob", glob])

    # Apply default ignore patterns
    for ignore_pattern in DEFAULT_IGNORE_PATTERNS:
        # rg 的 --glob 支持 “!pattern” 表示排除；这里把默认忽略模式转换为排除 glob。
        cmd.extend(["--glob", f"!{ignore_pattern}"])

    # Add multiline mode
    if multiline:
        cmd.extend(["-U", "--multiline-dotall"])

    # Execute ripgrep
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise on non-zero exit (no matches found)
        )

        # Check for errors (exit code 2 indicates error, 1 means no matches)
        if result.returncode == 2 or result.stderr:
            return f"Error: {result.stderr.strip()}"

        output = result.stdout

        # Apply head limit if specified
        if head_limit and output:
            lines = output.splitlines()
            output = "\n".join(lines[:head_limit])

        # Format the result
        reminders = generate_reminders(runtime)
        if output:
            return (
                f"Here's the result in {search_path}:\n\n```\n{output}\n```{reminders}"
            )
        else:
            return f"No matches found.{reminders}"

    except Exception as e:
        return f"Error: {str(e)}"
