import os
import re

import pexpect


class BashTerminal:
    """一个“常驻”的 bash 会话封装。

    与一次性 `subprocess.run` 不同，这里通过 pexpect 维持一个持续的 shell：
    - 可以保留 shell 内部状态（例如当前目录、已导出的环境变量等）；
    - 更贴近开发者在真实终端里连续输入命令的体验；
    - 通过自定义 PS1 提示符来判定命令何时执行完毕。
    """

    def __init__(self, cwd=None):
        """
        Initialize BashTerminal
        初始化 BashTerminal

        Args:
            cwd: Initial working directory, defaults to current directory
            cwd: 初始工作目录，默认为当前目录
        """
        self.cwd = cwd or os.getcwd()

        # Start bash shell
        # 启动 bash 子进程
        self.shell = pexpect.spawn("/bin/bash", encoding="utf-8", echo=False)

        # Set custom prompt for easy command completion detection
        # 设置固定提示符，便于判断命令何时执行完毕
        self.prompt = "BASH_TERMINAL_PROMPT> "
        self.shell.sendline(f'PS1="{self.prompt}"')
        self.shell.expect(self.prompt, timeout=5)

        # Change to specified directory
        # 若指定了目录，则切换到该目录
        if cwd:
            # 用 execute 统一走“发送命令 -> 等待 prompt”的逻辑
            self.execute(f'cd "{self.cwd}"')

    def execute(self, command):
        """
        Execute bash command and return output
        执行 bash 命令并返回输出

        Args:
            command: Command to execute
            command: 要执行的命令

        Returns:
            Command output result (string)
            命令输出结果（字符串）
        """
        # Send command
        # 发送命令到 shell
        self.shell.sendline(command)

        # Wait for prompt to appear, indicating command completion
        # 等待提示符再次出现，表示命令已执行完毕
        self.shell.expect(self.prompt, timeout=30)

        # Get output, removing command itself and prompt
        # 取「提示符之前」的内容作为输出（不含命令本身和提示符）
        output = self.shell.before

        # Clean output: remove command echo
        # 清理输出：去掉回显的命令行
        lines = output.split("\n")
        if lines and lines[0].strip() == command.strip():
            lines = lines[1:]

        # pexpect 可能保留一些空白与控制字符，这里做一次规整。
        result = "\n".join([line.strip() for line in lines]).strip()
        # Remove terminal control characters (e.g. ANSI color codes)
        # 去掉终端控制字符（如 ANSI 颜色码）
        result = re.sub(r"\x1b\[[0-9;]*m", "", result)
        return result

    def getcwd(self):
        """
        Get current working directory
        获取当前工作目录

        Returns:
            Absolute path of current working directory
            当前工作目录的绝对路径
        """
        result = self.execute("pwd")
        return result.strip()

    def close(self):
        """关闭 shell 会话（如果仍存活）。"""
        if self.shell.isalive():
            self.shell.sendline("exit")
            self.shell.close()

    def __del__(self):
        """Destructor, ensure shell is closed"""
        """析构函数，确保 shell 被正确关闭"""
        self.close()

    def __enter__(self):
        """Support with statement"""
        """支持 with 语句进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support with statement"""
        """支持 with 语句退出时关闭资源"""
        self.close()
