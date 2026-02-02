from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from deer_code.cli.theme import DEER_DARK_THEME


class CodeView(VerticalScroll):
    """Code view component with syntax highlighting.

    代码视图组件：用于在 TUI 中展示文本/代码，并提供语法高亮与行号。
    说明：保留英文原文（便于和上游 Textual/Rich 文档对照），并补充中文解释。
    """

    DEFAULT_CSS = """
    CodeView {
        height: 1fr;
    }

    CodeView #code-content {
        padding: 1 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 当前展示的“源文本”（通常是文件内容）。
        # 注意：这里的默认内容只是占位欢迎文案，真正使用时会通过 update_code() 覆盖。
        self.code = "# Welcome to DeerCode\n# Code will be displayed here\n\ndef hello_world():\n    print('Hello, World!')"
        # 当前代码对应的文件路径（用于推断 lexer / 也可用于 UI 展示）。
        self.file_path = None

    def compose(self) -> ComposeResult:
        # CodeView 内部只放一个 Static，用来承载 rich.Syntax 渲染出的高亮内容。
        # 之所以不用 Markdown，是因为这里更强调“代码块 + 行号 + lexer”能力。
        yield Static(id="code-content")

    def update_code(self, code: str, file_path: str = None) -> None:
        """Update code content and optionally the file path.

        更新代码内容，并可选更新 file_path（用于自动识别语言）。
        """
        self.code = code
        self.file_path = file_path

        # Auto-detect language from file path or default to python
        # 自动从文件路径推断 lexer（例如 .py/.ts/.md 等）。
        # 如果没有路径，则退化为纯文本显示（避免错误 lexer 导致高亮异常）。
        if file_path:
            lexer = Syntax.guess_lexer(file_path, code)
        else:
            lexer = "text"

        # Create syntax highlighted content
        # 使用 Rich 的 Syntax 来做语法高亮渲染（Textual 可直接显示 Rich renderable）。
        syntax = Syntax(
            code,
            lexer,
            theme="monokai",
            line_numbers=True,
            word_wrap=False,
            indent_guides=False,
            # 使用主题里的 boost 色作为背景，以保证深色主题下可读性更好。
            background_color=DEER_DARK_THEME.boost,
        )

        # 找到承载内容的 Static 并更新渲染对象。
        content_widget = self.query_one("#code-content", Static)
        content_widget.update(syntax)
