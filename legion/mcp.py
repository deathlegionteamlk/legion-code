import os
import json
import subprocess
import threading
from dataclasses import dataclass, field


@dataclass
class McpServerInfo:
    name: str
    command: str
    transport: str = "stdio"
    tools: list = field(default_factory=list)
    connected: bool = False


class McpClient:
    def __init__(self, server_name: str = "", command: str = "", transport: str = "stdio"):
        self.server_name = server_name
        self.command = command
        self.transport = transport
        self._process = None

    def connect(self):
        if self.command:
            try:
                self._process = subprocess.Popen(
                    self.command.split(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                return True
            except Exception:
                return False
        return False

    def list_tools(self) -> list:
        return []

    def execute_tool(self, tool_name: str, args: dict) -> str:
        return f"MCP tool {tool_name} not implemented"

    def disconnect(self):
        if self._process:
            self._process.terminate()
            self._process = None


class McpManager:
    def __init__(self):
        self.servers = {}
        self._tool_registry = {}
        self._clients = {}

    def register_server(self, name: str, command: str, transport: str = "stdio"):
        self.servers[name] = McpServerInfo(name=name, command=command, transport=transport, connected=False)
        client = McpClient(server_name=name, command=command, transport=transport)
        client.connect()
        self._clients[name] = client

    def remove_server(self, name: str):
        if name in self.servers:
            del self.servers[name]
        if name in self._clients:
            self._clients[name].disconnect()
            del self._clients[name]
        self._tool_registry = {k: v for k, v in self._tool_registry.items() if not k.startswith(f"mcp_{name}_")}

    def list_servers(self) -> list:
        return [{"name": s.name, "command": s.command, "transport": s.transport, "connected": s.connected, "tools_count": len(s.tools)} for s in self.servers.values()]

    def discover_tools(self, name: str) -> list:
        server = self.servers.get(name)
        if not server:
            return []
        client = self._clients.get(name)
        if client:
            tools = client.list_tools()
            server.tools = tools
            server.connected = True
            return tools
        return []

    def discover_all_tools(self):
        for name in self.servers:
            self.discover_tools(name)

    def get_mcp_tool_schemas(self) -> list:
        schemas = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                schema = {
                    "type": "function",
                    "function": {
                        "name": f"mcp_{server_name}_{tool.get('name', 'unknown')}",
                        "description": tool.get("description", f"MCP tool from {server_name}"),
                        "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
                    }
                }
                schemas.append(schema)
                self._tool_registry[schema["function"]["name"]] = {"server": server_name, "tool": tool}
        return schemas

    def execute_tool(self, tool_name: str, args: dict) -> str:
        tool_info = self._tool_registry.get(tool_name)
        if not tool_info:
            return f"Error: unknown MCP tool '{tool_name}'"
        server = self.servers.get(tool_info["server"])
        if not server:
            return f"Error: MCP server '{tool_info['server']}' not found"
        client = self._clients.get(tool_info["server"])
        if client:
            return client.execute_tool(tool_info["tool"]["name"], args)
        return f"Error: MCP client for '{tool_info['server']}' not connected"

    def get_all_tools(self) -> list:
        tools = []
        for server_name, server in self.servers.items():
            for tool in server.tools:
                tools.append({
                    "name": f"mcp_{server_name}_{tool.get('name', 'unknown')}",
                    "description": tool.get("description", f"MCP tool from {server_name}"),
                    "input_schema": tool.get("input_schema", {"type": "object", "properties": {}}),
                })
        return tools