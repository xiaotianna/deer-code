"""editor 组件子包。

用于在 Textual TUI 中提供“文件/代码查看”相关组件：
- `CodeView`: 代码渲染（语法高亮、行号、可滚动）
- `EditorTabs`: 多标签容器（打开文件/欢迎页）
"""

from .code_view import CodeView
from .editor_tabs import EditorTabs

__all__ = ["CodeView", "EditorTabs"]
