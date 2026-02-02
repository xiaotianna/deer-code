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

        Args:
            cwd: Initial working directory, defaults to current directory
        """
        self.cwd = cwd or os.getcwd()

        # Start bash shell
        self.shell = pexpect.spawn("/bin/bash", encoding="utf-8", echo=False)

        # Set custom prompt for easy command completion detection
        self.prompt = "BASH_TERMINAL_PROMPT> "
        self.shell.sendline(f'PS1="{self.prompt}"')
        self.shell.expect(self.prompt, timeout=5)

        # Change to specified directory
        if cwd:
            # 用 execute 统一走“发送命令 -> 等待 prompt”的逻辑
            self.execute(f'cd "{self.cwd}"')

    def execute(self, command):
        """
        Execute bash command and return output

        Args:
            command: Command to execute

        Returns:
            Command output result (string)
        """
        # Send command
        self.shell.sendline(command)

        # Wait for prompt to appear, indicating command completion
        self.shell.expect(self.prompt, timeout=30)

        # Get output, removing command itself and prompt
        output = self.shell.before

        # Clean output: remove command echo
        lines = output.split("\n")
        if lines and lines[0].strip() == command.strip():
            lines = lines[1:]

        # pexpect 可能保留一些空白与控制字符，这里做一次规整。
        result = "\n".join([line.strip() for line in lines]).strip()
        # Remove terminal control characters
        result = re.sub(r"\x1b\[[0-9;]*m", "", result)
        return result

    def getcwd(self):
        """
        Get current working directory

        Returns:
            Absolute path of current working directory
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
        self.close()

    def __enter__(self):
        """Support with statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support with statement"""
        self.close()
