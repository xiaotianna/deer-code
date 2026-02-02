from pathlib import Path
from typing import Literal

TextEditorCommand = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
]


class TextEditor:
    """A standalone text editor tool for AI agents to interact with files.

    This tool allows viewing, creating, and editing files with proper error handling
    and suggestions to help AI agents learn from mistakes.

    中文说明（保留英文原文）：
    这是一个“纯 Python 实现”的文本编辑器能力封装，供上层 `text_editor` 工具调用。
    它提供：
    - view：读取并带行号展示（便于精确引用与替换）
    - write_file：写入文件并自动创建父目录
    - str_replace：基于字符串的全量替换（不做 AST/patch 级别 diff）
    - insert：按“行号之后插入”的规则插入文本
    """

    def validate_path(self, command: TextEditorCommand, path: Path):
        """Check that the path is absolute.

        只允许绝对路径的原因：
        - Agent 往往缺少“当前工作目录”的稳定概念；
        - 使用绝对路径可以减少误写到未知位置的风险；
        - 也更容易在工具返回中明确指向同一个文件。

        中文补充（英文原文保留）：这里不区分 command 类型，统一只做“是否绝对路径”的校验；
        其他校验（是否存在/是否文件）由各具体方法（view/insert/str_replace）分别处理。

        Args:
            command: The command to execute.
            path: The path to the file or directory.

        Raises:
            ValueError: If path is not absolute.
        """

        # 判断是否是绝对路径，mac/linux通过 “/”开头
        if not path.is_absolute():
            # 转换为绝对路径，Path("") / path 在大多数情况下等价于“去掉前面的 ./ 之类前缀”
            suggested_path = Path("") / path
            raise ValueError(
                f"The path {path} is not an absolute path, it should start with `/`. Do you mean {suggested_path}?"
            )

    def view(self, path: Path, view_range: list[int] | None = None):
        """View the content of a file.

        中文说明（保留英文原文）：
        - 默认读取全文件；如果提供 view_range=[start,end] 则截取指定范围；
        - start/end 是 1-based；end=-1 表示一直读到文件末尾；
        - 返回值会附加行号（模拟 `cat -n`），便于后续精确定位替换/插入。

        Args:
            path: The absolute path to the file.
            view_range: Optional list of two integers [start, end] for line range.
                Line numbers are 1-indexed. Use -1 for end line to read to EOF.

        Returns:
            str: The file content with line numbers.

        Raises:
            ValueError: If file doesn't exist, is not a file, or view_range is invalid.
        """

        # 判断这个路径在文件系统里是否存在
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")

        # 判断这个路径在文件系统里是否是一个文件
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # 读取文件内容
        file_content = self.read_file(path)
        # 初始化行号为1
        init_line = 1
        # 如果提供了view_range，则根据view_range截取文件内容
        if view_range:
            # len(view_range) != 2：要求 view_range 必须是长度为 2 的列表（形如 [start, end]），否则就不合法。
            # 条件2：要求列表里的两个元素都必须是 int 类型（整数），只要有一个不是整数（比如字符串/浮点数），就判定不合法。
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                raise ValueError(
                    "Invalid `view_range`. It should be a list of two integers."
                )
            # 将文件内容按行分割
            file_lines = file_content.split("\n")
            # 获取文件总行数
            n_lines_file = len(file_lines)
            # 获取view_range的开始和结束行号
            init_line, final_line = view_range

            # 验证开始行号是否合法
            if init_line < 1 or init_line > n_lines_file:
                raise ValueError(
                    f"Invalid `view_range`: {view_range}. The start line `{init_line}` should be within the range of lines in the file: {[1, n_lines_file]}"
                )

            # 验证结束行号是否合法
            if final_line != -1 and (
                final_line < init_line or final_line > n_lines_file
            ):
                if final_line > n_lines_file:
                    final_line = n_lines_file
                else:
                    raise ValueError(
                        f"Invalid `view_range`: {view_range}. The end line `{final_line}` should be -1 or "
                        f"within the range of lines in the file: {[init_line, n_lines_file]}"
                    )

            # 根据view_range截取文件内容
            # view_range = [2, -1]，final_line==-1，表示读取到文件末尾
            if final_line == -1:
                file_content = "\n".join(file_lines[init_line - 1 :])
            else:
                file_content = "\n".join(file_lines[init_line - 1 : final_line])

        return self._content_with_line_numbers(file_content, init_line=init_line)

    # 把文件里所有出现的 old_str 全部替换（可能是 0 次、1 次、也可能是多次）
    """
    - 如果你确定只应该有一处要改：
        - 最好让 old_str 写得“长一点、具体一点”，带上上下文，让它只在唯一位置出现。
        - 比如不要只写 "foo", 而是写整行：'return foo(bar)'。
    - 如果你就是想批量替换多处（比如把所有 "TODO" 都删掉）：
        - 那就直接传一个短的 old_str（比如 "TODO"），然后看返回的 occurrences 知道改了多少处。
    """
    def str_replace(self, path: Path, old_str: str, new_str: str | None):
        """Replace all occurrences of old_str with new_str in the file.

        说明：
        - 这里使用 `str.replace` 是“全量替换”，不做语义级 diff；
        - 若 `old_str` 过短/不唯一，可能替换到多处，因此调用方应提供足够上下文让它更唯一。

        中文补充（英文原文保留）：
        - 当前实现并不会强制 old_str “唯一”，而是会替换所有出现次数；
          因此更安全的用法是：old_str 带上足够多的前后文，使其在文件中尽量唯一。

        Args:
            path: The path to the file.
            # 要替换的字符串。如果`old_str`在文件中不是唯一的，则编辑将失败。提供一个更大的字符串和更多的上下文，使其独一无二。
            old_str: The string to be replaced. The edit will FAIL if `old_str` is not unique in the file. Provide a larger string with more surrounding context to make it unique.
            # 要替换的新字符串。如果为None，则old_str将被删除。
            new_str: The replacement string. If None, old_str will be removed.

        Returns:
            # 返回替换的次数。
            int: The count of replacements.

        Raises:
            # 如果文件不存在，则抛出异常。
            ValueError: If file doesn't exist, is not a file, or old_str not found.
        """
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # 读取文件内容
        file_content = self.read_file(path)

        # 检查old_str是否存在于文件中
        if old_str not in file_content:
            raise ValueError(f"String not found in file: {path}")

        # 如果new_str为None，则new_str为空字符串
        if new_str is None:
            new_str = ""

        # 替换old_str为new_str
        new_content = file_content.replace(old_str, new_str)

        # 统计old_str出现的次数
        """
        统计次数是为了给 Agent 提供明确的反馈，让它知道替换操作的结果。

        在 tool.py 里，text_editor_tool 会返回类似这样的消息：
           return f"Successfully replaced {occurrences} occurrences in {_path}.{reminders}"

        如果返回“替换了 3 处”，Agent 就能判断：
            - 如果期望只替换 1 处 → 可能 old_str 不够唯一，需要提供更多上下文
            -如果期望替换多处 → 操作正常
        如果 Agent 发现替换了多出，可能会：
            -先 view 文件，确认哪些地方被改了
            -如果改错了，再用更精确的 old_str（带更多上下文）重新替换
        """
        occurrences = file_content.count(old_str)

        # 将修改后的内容写回文件
        self.write_file(path, new_content)

        return occurrences

    def insert(self, path: Path, insert_line: int, new_str: str):
        """Insert text at a specific line in the file.

        注意：insert_line 的语义是“在某一行之后插入”，并支持 0 表示文件开头插入。
        为了减少歧义，这里把插入位置限制在 [0, len(lines)] 之间。

        中文补充（英文原文保留）：
        - insert_line=0：插入到文件最开头（成为新的第 1 行）
        - insert_line=N>0：插入到“原第 N 行之后”（实现上等价于 list.insert(N, ...)）
        - 这里的 N 与 view 的行号口径一致（1-based 语义），但实现用的是 0-based list 索引；
          因此代码里会有看起来像“插入到 index=insert_line”的写法。

        Args:
            path: The path to the file to modify.
            insert_line: The line number after which to insert (0 for beginning).
            new_str: The text to insert.

        Raises:
            ValueError: If file doesn't exist, is not a file, or insert_line is invalid.
        """
        if not path.exists():
            raise ValueError(f"File does not exist: {path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        # Read the file content
        file_content = self.read_file(path)
        lines = file_content.splitlines()

        # 验证insert_line是否合法
        if insert_line < 0:
            raise ValueError(
                f"Invalid insert_line: {insert_line}. Line number must be >= 0."
            )

        # 验证insert_line是否大于文件总行数
        if insert_line > len(lines):
            raise ValueError(
                f"Invalid insert_line: {insert_line}. Line number cannot be greater than the number of lines in the file ({len(lines)})."
            )

        # 插入新文本
        if insert_line == 0:
            # 插入到文件开头
            lines.insert(0, new_str)
        else:
            # 插入到指定行之后
            lines.insert(insert_line, new_str)

        # 将行合并为新的文件内容
        new_content = "\n".join(lines)

        # 将修改后的内容写回文件
        self.write_file(path, new_content)

    # read_file：底层“读原始文件内容”的工具函数
    # view：面向 Agent 的“带行号、可截取区间的查看接口”，内部会调用 read_file
    def read_file(self, path: Path):
        """Read the content of a file.

        中文说明（保留英文原文）：薄封装，统一异常为 ValueError，便于上层工具捕获并返回可读错误信息。

        Args:
            path: The path to the file to read.

        Returns:
            str: The file content.

        Raises:
            ValueError: If file cannot be read.
        """
        try:
            return path.read_text()
        except Exception as e:
            raise ValueError(f"Error reading {path}: {e}")

    def write_file(self, path: Path, content: str):
        """Write content to a file.

        写入前会确保父目录存在（mkdir -p 语义），便于一次性创建新文件路径。

        中文补充（英文原文保留）：这里使用 Path.write_text 写入（一次性覆盖），不做增量 patch。

        Args:
            path: The path to the file to write.
            content: The content to write.

        Raises:
            ValueError: If file cannot be written.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        except Exception as e:
            raise ValueError(f"Error writing to {path}: {e}")

    # 给传入的文本每一行加上行号，行号右对齐
    def _content_with_line_numbers(
        self,
        file_content: str,
        init_line: int = 1,
    ):
        # 输出格式与 `cat -n` 类似：行号右对齐，便于模型引用具体位置。
        # splitlines按照\n换行分割
        lines = file_content.splitlines()
        # i + init_line行号
        # :>3 右对齐，宽度为3
        # 最终形如：" 1 line1"、" 10 line10"
        lines = [f"{i + init_line:>3} {line}" for i, line in enumerate(lines)]
        file_content = "\n".join(lines)
        return file_content
