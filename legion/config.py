import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    api_base: str = "https://openrouter.ai/api/v1"
    model: str = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    max_tool_call_iterations: int = 50
    session_dir: str = ""
    request_timeout: int = 120
    history_limit: int = 20
    permission_mode: str = "default"
    allowed_tools: list = field(default_factory=lambda: ["*"])
    denied_tools: list = field(default_factory=list)
    output_format: str = "text"
    json_schema: Optional[dict] = None
    worktree_dir: str = ""
    bg_enabled: bool = False
    agents_config: Optional[dict] = None
    resume_session: Optional[str] = None
    max_turns: int = 0
    add_dirs: list = field(default_factory=list)
    system_prompt_extra: str = ""
    effort_level: str = "medium"
    hook_configs: list = field(default_factory=list)
    skill_name: str = ""
    mcp_servers: list = field(default_factory=list)
    list_mode: bool = False
    print_mode: bool = False
    save_sessions: bool = True
    compact_mode: bool = False

    github_token: str = ""
    github_repo: str = ""
    encryption_key: str = ""
    obfuscate_on_build: bool = False
    deploy_target: str = "local"
    database_url: str = ""
    workflow_dir: str = ""
    benchmark_enabled: bool = False
    context_budget: int = 8192

    def __post_init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not self.github_token:
            self.github_token = os.environ.get("GITHUB_TOKEN", "")
        if not self.session_dir:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.session_dir = os.path.join(base, "sessions")
        if not self.workflow_dir:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.workflow_dir = os.path.join(base, "workflows")
        if self.allowed_tools == ["*"]:
            self.allowed_tools = []