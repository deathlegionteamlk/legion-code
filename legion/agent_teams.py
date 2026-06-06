import json
import threading
from legion.config import Config
from legion.subagent import SubAgent


AGENT_TYPES = {
    "planner": {"tools": [], "prompt": "You are a planning agent. Break down tasks into clear steps."},
    "coder": {"tools": ["read_file", "write_file", "edit_file", "run_command"], "prompt": "You are a coding agent. Write and test code."},
    "reviewer": {"tools": ["read_file", "grep_search", "explore_directory"], "prompt": "You are a code reviewer. Analyze code for issues."},
    "tester": {"tools": ["read_file", "run_command", "grep_search"], "prompt": "You are a testing agent. Write and run tests."},
    "researcher": {"tools": ["internet_search"], "prompt": "You are a research agent. Search for information."},
    "security-reviewer": {"tools": ["read_file", "grep_search", "explore_directory"], "prompt": "You are a security reviewer. Find vulnerabilities."},
}


class Team:
    def __init__(self, config: Config = None, agents_config: dict = None):
        self.config = config or Config()
        self.lead_agent = None
        self.sub_agents = {}
        self.messages = []
        self.task_history = []
        if agents_config:
            self._build_from_config(agents_config)

    def _build_from_config(self, agents_config: dict):
        for name, cfg in agents_config.items():
            agent_type = cfg.get("type", "planner")
            template = AGENT_TYPES.get(agent_type, AGENT_TYPES["planner"])
            tool_names = cfg.get("tools", template["tools"])
            prompt = cfg.get("prompt", template["prompt"])
            tools = []
            for tn in tool_names:
                try:
                    from legion.tools import get_tool
                    t = get_tool(tn)
                    if t:
                        tools.append(t)
                except Exception:
                    pass
            sub = SubAgent(name=name, config=self.config, tools=tools, system_prompt=prompt)
            self.sub_agents[name] = sub

    def add_agent(self, name: str, agent_type: str = "planner", tools: list = None, prompt: str = ""):
        template = AGENT_TYPES.get(agent_type, AGENT_TYPES["planner"])
        tool_list = tools if tools else template["tools"]
        prompt_text = prompt or template["prompt"]
        resolved_tools = []
        for tn in tool_list:
            try:
                from legion.tools import get_tool
                t = get_tool(tn)
                if t:
                    resolved_tools.append(t)
            except Exception:
                pass
        sub = SubAgent(name=name, config=self.config, tools=resolved_tools, system_prompt=prompt_text)
        self.sub_agents[name] = sub

    def remove_agent(self, name: str):
        if name in self.sub_agents:
            self.sub_agents[name].close()
            del self.sub_agents[name]

    def get_agent(self, name: str) -> SubAgent:
        return self.sub_agents.get(name)

    def get_agent_names(self) -> list:
        return list(self.sub_agents.keys())

    def distribute_task(self, goal: str) -> list:
        if not self.sub_agents:
            return [{"error": "No sub-agents in team"}]
        results = []
        for name, sub in self.sub_agents.items():
            sub.set_task(goal)
            result = sub.run()
            results.append({"agent": name, "result": result[:500] if result else "no output"})
        self.task_history.append({"goal": goal, "results": results})
        return results

    def distribute_tasks(self, tasks: list) -> list:
        results = []
        for task in tasks:
            agent_type = task.get("agent_type", "planner")
            description = task.get("description", "no description")
            sub = self.sub_agents.get(agent_type)
            if sub:
                sub.set_task(description)
                result = sub.run()
                results.append({"agent": agent_type, "task": description, "result": result[:500] if result else "no output"})
            else:
                for name, sub in self.sub_agents.items():
                    sub.set_task(description)
                    result = sub.run()
                    results.append({"agent": name, "task": description, "result": result[:500] if result else "no output"})
                break
        self.task_history.append({"tasks": tasks, "results": results})
        return results

    def distribute_parallel(self, tasks: list) -> list:
        results = []
        threads = []
        results_lock = threading.Lock()

        def run_task(sub, task_desc):
            r = sub.run()
            with results_lock:
                results.append({"agent": sub.name, "task": task_desc, "result": r[:500] if r else "no output"})

        for task in tasks:
            agent_type = task.get("agent_type", "planner")
            description = task.get("description", "no description")
            sub = self.sub_agents.get(agent_type) or next(iter(self.sub_agents.values()), None)
            if sub:
                sub.set_task(description)
                t = threading.Thread(target=run_task, args=(sub, description))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()
        return results

    def get_summary(self) -> str:
        lines = [f"Team with {len(self.sub_agents)} agents:"]
        for name, sub in self.sub_agents.items():
            lines.append(f"  {name}: {sub.result[:100] if sub.result else 'idle'}")
        return "\n".join(lines)

    def close(self):
        for sub in self.sub_agents.values():
            sub.close()