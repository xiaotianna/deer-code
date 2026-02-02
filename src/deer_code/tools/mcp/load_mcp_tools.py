"""从配置加载 MCP（Model Context Protocol）工具。

MCP 的作用是把“外部能力”以统一的 tool 形式接入 Agent：
- 配置中声明 MCP servers（传输方式/URL/鉴权等）；
- `MultiServerMCPClient` 负责连接多个 server 并拉取工具列表；
- 最终返回的 tools 会被注入到 Agent 的 tool 列表中（作为扩展能力）。
"""

from langchain_mcp_adapters.client import MultiServerMCPClient

from deer_code.config.config import get_config_section


async def load_mcp_tools():
    """Load MCP tools from the config."""
    # 读取配置中的 tools.mcp_servers（可能为空，表示未启用 MCP）。
    servers = get_config_section(["tools", "mcp_servers"])
    if not servers:
        return []
    # MultiServerMCPClient 会并行管理多个 server，并统一暴露 get_tools().
    client = MultiServerMCPClient(servers)
    return await client.get_tools()


if __name__ == "__main__":
    import asyncio

    asyncio.run(load_mcp_tools())
