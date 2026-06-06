import json
from legion.config import Config
from legion.provider import Provider


class SubAgent:
    def __init__(self, name: str, config: Config = None, tools: list = None, system_prompt: str = ""):
        self.name = name
        self.config = config or Config()
        self.provider = Provider(self.config)
        self.history = []
        self.tools = tools or []
        self.system_prompt = system_prompt
        self.result = ""

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def set_task(self, task: str):
        self.history = []
        self.add_message("user", task)

    def run(self) -> str:
        if not self.history:
            return ""
        try:
            response = self.provider.chat(
                self.history,
                system_prompt=self.system_prompt,
                tools=self.tools if self.tools else None,
            )
            message = self.provider.extract_assistant_message(response)
            content = message.get("content", "")
            self.result = content
            self.add_message("assistant", content)
            return content
        except Exception as e:
            error_msg = f"SubAgent {self.name} error: {e}"
            self.result = error_msg
            return error_msg

    def run_with_tools(self, tool_executor) -> str:
        if not self.history:
            return ""
        try:
            response = self.provider.chat(
                self.history,
                system_prompt=self.system_prompt,
                tools=self.tools if self.tools else None,
            )
            message = self.provider.extract_assistant_message(response)
            tool_calls = self.provider.extract_tool_calls(message)
            content = message.get("content", "")
            if content:
                self.add_message("assistant", content)
            if tool_calls:
                for tc in tool_calls:
                    name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    result = tool_executor(name, args)
                    self.add_message("tool", result)
                response2 = self.provider.chat(self.history, system_prompt=self.system_prompt)
                msg2 = self.provider.extract_assistant_message(response2)
                content2 = msg2.get("content", "")
                self.result = content2
                self.add_message("assistant", content2)
                return content2
            self.result = content
            return content
        except Exception as e:
            error_msg = f"SubAgent {self.name} error: {e}"
            self.result = error_msg
            return error_msg

    def close(self):
        self.provider.close()

    def get_summary(self) -> str:
        return f"SubAgent '{self.name}': {self.result[:200] if self.result else 'no result'}"