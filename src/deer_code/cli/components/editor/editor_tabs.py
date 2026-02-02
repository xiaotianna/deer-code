from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Markdown, TabbedContent, TabPane

from .code_view import CodeView


class EditorTabs(TabbedContent):
    """VSCode 风格的“多标签编辑器”容器。

    英文说明（原内容保留在代码中）：TabbedContent/TabPane 是 Textual 提供的选项卡组件。
    中文补充：这个类负责维护“路径 -> TabPane”的映射，并提供打开文件/打开欢迎页等入口。
    """

    DEFAULT_CSS = """
    EditorTabs {
        height: 1fr;
    }
    """

    # 维护已打开的文件 Tab：key 是文件路径，value 是对应的 TabPane 实例。
    # 注意：这里写在类属性上，等价于“所有 EditorTabs 实例共享一份字典”，
    # 在本项目通常只有一个 EditorTabs，所以问题不大；若未来支持多窗口，建议改为实例属性。
    tab_map: dict[str, TabPane] = {}

    def open_file(self, path: str, file_text: str = None):
        """打开一个文件到标签页中（若已打开则切换到该标签）。

        Args:
            path: 文件路径（当前实现允许相对/绝对，最终会被 open() 使用）。
            file_text: 可选的文件内容；若传入则不再从磁盘读取，直接用该内容刷新视图。
        """
        tab = self._find_tab_by_path(path)
        if tab is None:
            tab = EditorTab(path)
            self.tab_map[path] = tab
            self.add_pane(tab)
        # 设置当前活跃 Tab（TabbedContent 用 active=id 来切换）
        self.active = tab.id
        # 刷新 Tab 内容（文件内容优先用传入的 file_text）
        tab.update(file_text)
        return tab

    def open_welcome(self):
        """打开欢迎页（docs/welcome.md）到一个固定的标签。"""
        tab = TabPane(title="Welcome", id="welcome-tab")
        # 这里读取的是仓库内的 docs/welcome.md，用 Markdown 组件渲染展示。
        # 如果未来要支持中文欢迎页，可以考虑读取 docs/welcome_zh.md 或根据配置选择。
        markdown = Markdown(Path("docs/welcome.md").read_text(), id="welcome-view")
        self.add_pane(tab)
        tab.mount(markdown)
        self.active = tab.id

    def _find_tab_by_path(self, path: str) -> TabPane | None:
        # 查找已打开文件的 Tab；当前实现仅做字典查找。
        return self.tab_map.get(path)


class EditorTab(TabPane):
    """单个文件的编辑/预览 Tab。

    一个 EditorTab 里挂载一个 CodeView，用于显示当前文件内容（带语法高亮）。
    """

    def __init__(self, path: str, **kwargs):
        # Tab 标题只显示文件名（不显示完整路径），避免标题过长。
        title = extract_filename(path)
        super().__init__(title=title, **kwargs)
        # 保存文件路径，用于后续读取文件和推断 lexer。
        self.path = path

    def compose(self) -> ComposeResult:
        # 每个 Tab 内容：一个 CodeView（可滚动）。
        yield CodeView(id="code-view")

    def update(self, file_text: str | None = None):
        """刷新标签页显示内容。

        Args:
            file_text: 若提供则直接使用；否则从 self.path 读取磁盘内容。
        """
        code_view = self.query_one("#code-view", CodeView)
        if file_text is not None:
            code_view.update_code(file_text, self.path)
        else:
            # 从磁盘读取文件内容并展示。
            # 注意：这里未显式指定编码，默认使用系统默认编码（macOS 通常是 utf-8）。
            with open(self.path, "r") as file:
                code = file.read()
                code_view.update_code(code, self.path)


def extract_filename(path: str) -> str:
    """从路径中提取文件名（不含目录部分）。"""
    _path = Path(path)
    return _path.name
