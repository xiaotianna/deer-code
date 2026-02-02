"""`text_editor` tool: provide controlled file view/edit capabilities for the agent.

`text_editor` 工具：给 Agent 提供可控的文件查看/编辑能力。

Design notes (English original kept):
- Only absolute paths are allowed to reduce ambiguity and accidental writes.
- Editing is split into atomic commands: view / create / str_replace / insert.
  This helps the model iterate safely (view more context when replace/insert fails).
- Append reminders to tool outputs to nudge the agent to finish TODO workflow.

设计要点（中文补充）：
- 只允许绝对路径，避免在不明确位置写文件。
- 把编辑操作拆成更“原子”的命令：view / create / str_replace / insert，
  这样模型更容易按步骤完成修改、并在失败时回退到 view 获取更多上下文。
- 在每次工具返回末尾追加 reminders，用于提示 todo 工作流收尾。
"""

from pathlib import Path
from typing import Optional

from langchain.tools import ToolRuntime, tool

from deer_code.tools.reminders import generate_reminders

from .text_editor import TextEditor


@tool("text_editor", parse_docstring=True)
def text_editor_tool(
    runtime: ToolRuntime,
    command: str,
    path: str,
    file_text: Optional[str] = None,
    view_range: Optional[list[int]] = None,
    old_str: Optional[str] = None,
    new_str: Optional[str] = None,
    insert_line: Optional[int] = None,
):
    """
    A text editor tool supports view, create, str_replace, insert.

    - `view` again when you fail to perform `str_replace` or `insert`.
    - `create` can also be used to overwrite an existing file.
    - `str_replace` can also be used to delete text in the file.

    中文说明（保留英文原文）：
    - 本工具提供 4 类原子操作：查看(view)、创建/覆盖(create)、字符串替换(str_replace)、按行插入(insert)。
    - 当替换/插入失败时，推荐先 view 获取更大上下文，提升定位与替换的确定性。
    - create 会写入文件内容；目录不存在会自动创建（由 TextEditor.write_file 负责）。

    Args:
        command: One of "view", "create", "str_replace", "insert".
        path: The absolute path to the file. Only absolute paths are supported. Automatically create the directories if it doesn't exist.
        file_text: Only applies for the "create" command. The text to write to the file.
        view_range:
            Only applies for the "view" command.
            An array of two integers specifying the start and end line numbers to view.
            Line numbers are 1-indexed, and -1 for the end line means read to the end of the file.
        old_str: Only applies for the "str_replace" command. The text to replace (must match exactly, including whitespace and indentation).
        new_str: Only applies for the "str_replace" and "insert" commands. The new text to insert in place of the old text.
        insert_line: Only applies for the "insert" command. The line number after which to insert the text (0 for beginning of file).

    command：“视图”、“创建”、“str_replace”、“插入”之一。
    path：文件的绝对路径。仅支持绝对路径。如果目录不存在，则自动创建。
    file_text：仅适用于“create”命令。要写入文件的文本。
    view_range：
        仅适用于“视图”命令。
        一个由两个整数组成的数组，指定要查看的开始和结束行号。
        行号为1索引，结束行为-1表示读取到文件末尾。
    old_str：仅适用于“str_replace”命令。要替换的文本（必须完全匹配，包括空格和缩进）。
    new_str：仅适用于“str_replace”和“insert”命令。插入新文本以代替旧文本。
    insert_line：仅适用于“insert”命令。插入文本的行号（文件开头为0）。
    """
    _path = Path(path)
    reminders = generate_reminders(runtime)
    try:
        editor = TextEditor()
        # 统一在入口处校验路径合法性（目前仅校验必须为绝对路径）。
        editor.validate_path(command, _path)
        if command == "view":
            # 返回内容格式模拟 `cat -n`，便于模型在后续 str_replace/insert 时引用行号与上下文。
            return f"Here's the result of running `cat -n` on {_path}:\n\n```\n{editor.view(_path, view_range)}\n```{reminders}"
        elif command == "str_replace" and old_str is not None and new_str is not None:
            occurrences = editor.str_replace(_path, old_str, new_str)
            return f"Successfully replaced {occurrences} occurrences in {_path}.{reminders}"
        elif command == "insert" and insert_line is not None and new_str is not None:
            editor.insert(_path, insert_line, new_str)
            return f"Successfully inserted text at line {insert_line} in {path}.{reminders}"
        elif command == "create":
            if _path.is_dir():
                return f"Error: the path {_path} is a directory. Please provide a valid file path.{reminders}"
            # create 既可用于新建文件，也可用于覆盖已有文件（由上层提示词约束其使用方式）。
            editor.write_file(_path, file_text if file_text is not None else "")
            return f"File successfully created at {_path}.{reminders}"
        else:
            return f"Error: invalid command: {command}"
    except Exception as e:
        return f"Error: {e}"
