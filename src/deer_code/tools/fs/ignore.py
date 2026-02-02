"""文件/目录忽略规则集合（供 ls/grep/tree 等工具复用）。

这些模式用于：
- 默认隐藏依赖目录、构建产物、缓存、版本控制目录等“噪音”；
- 降低工具输出规模，让模型更聚焦在业务代码；
- 同时减少搜索/遍历时的性能开销。
"""

DEFAULT_IGNORE_PATTERNS = [
    # Version Control
    ".git/**",
    ".svn/**",
    ".hg/**",
    # Dependencies
    "node_modules/**",
    "bower_components/**",
    "vendor/**",
    "packages/**",
    # Python
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".Python",
    "venv/**",
    ".venv/**",
    "env/**",
    ".env/**",
    "ENV/**",
    "*.egg-info/**",
    ".eggs/**",
    "dist/**",
    "build/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".tox/**",
    # JavaScript/TypeScript
    ".next/**",
    ".nuxt/**",
    "out/**",
    ".cache/**",
    ".parcel-cache/**",
    ".turbo/**",
    # Build outputs
    "dist/**",
    "build/**",
    "target/**",
    "bin/**",
    "obj/**",
    # IDE/Editor
    ".vscode/**",
    ".idea/**",
    "*.swp",
    "*.swo",
    "*~",
    # Logs
    "*.log",
    "logs/**",
    "*.log.*",
    # Coverage
    "coverage/**",
    ".coverage",
    ".nyc_output/**",
    "htmlcov/**",
    # Rust
    "target/**",
    "Cargo.lock",
    # Go
    "go.sum",
    # Ruby
    ".bundle/**",
    # Java
    "*.class",
    ".gradle/**",
    ".mvn/**",
    # Temporary files
    "tmp/**",
    "temp/**",
    "*.tmp",
    "*.bak",
    # OS files
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
]
