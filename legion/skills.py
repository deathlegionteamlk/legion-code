import os
import json
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Skill:
    name: str
    description: str = ""
    allowed_tools: list = field(default_factory=list)
    argument_hint: str = ""
    body: str = ""


BUNDLED_SKILLS = {
    "review": Skill(
        name="review",
        description="Deep code review of the working tree",
        allowed_tools=["read_file", "grep_search", "explore_directory", "run_command"],
        argument_hint="<path>",
        body="Review the code at the specified path or whole workspace. Analyze code quality, potential bugs, style issues, and suggest improvements.",
    ),
    "test": Skill(
        name="test",
        description="Run tests and analyze results",
        allowed_tools=["run_command", "read_file", "grep_search"],
        argument_hint="<command>",
        body="Run the specified test command, capture results, analyze failures, and suggest fixes.",
    ),
    "security-review": Skill(
        name="security-review",
        description="Security audit of the codebase",
        allowed_tools=["read_file", "grep_search", "explore_directory", "internet_search"],
        argument_hint="<path>",
        body="Audit the codebase for security vulnerabilities including injection flaws, hardcoded secrets, unsafe deserialization, and permission issues.",
    ),
    "init": Skill(
        name="init",
        description="Scan project and initialize Legion context",
        allowed_tools=["read_file", "explore_directory", "run_command"],
        argument_hint="",
        body="Scan the project directory structure, identify key files (README, configs, entry points), and create LEGION.md with project context.",
    ),
    "refactor": Skill(
        name="refactor",
        description="Refactor code for improved structure and maintainability",
        allowed_tools=["read_file", "write_file", "edit_file", "explore_directory", "run_command"],
        argument_hint="<path>",
        body="Analyze the code at the given path and propose/apply refactoring improvements. Extract duplicated logic, simplify complex functions, improve naming, and enforce single responsibility.",
    ),
    "debug": Skill(
        name="debug",
        description="Debug code issues and fix bugs",
        allowed_tools=["read_file", "edit_file", "run_command", "grep_search", "internet_search"],
        argument_hint="<error-or-issue>",
        body="Investigate the reported issue or error. Examine relevant source files, run diagnostics, identify root cause, and implement a fix.",
    ),
    "optimize": Skill(
        name="optimize",
        description="Optimize code for performance",
        allowed_tools=["read_file", "edit_file", "run_command", "explore_directory"],
        argument_hint="<path>",
        body="Analyze code performance bottlenecks. Suggest and apply optimizations including algorithm improvements, caching, reduced allocations, and better data structures.",
    ),
    "document": Skill(
        name="document",
        description="Generate or update documentation",
        allowed_tools=["read_file", "write_file", "edit_file", "explore_directory", "run_command"],
        argument_hint="<path>",
        body="Scan the codebase at the given path and generate comprehensive documentation. Add docstrings, create README files, and document APIs and modules.",
    ),
    "deploy": Skill(
        name="deploy",
        description="Deploy application to target environment",
        allowed_tools=["read_file", "write_file", "run_command", "internet_search"],
        argument_hint="<target>",
        body="Prepare and execute deployment to the specified target. Generate Dockerfiles, docker-compose configs, or cloud deployment scripts as needed.",
    ),
    "architect": Skill(
        name="architect",
        description="Design software architecture",
        allowed_tools=["read_file", "write_file", "explore_directory", "internet_search"],
        argument_hint="<requirements>",
        body="Analyze requirements and design a software architecture. Consider components, data flow, API design, module boundaries, and technology choices.",
    ),
    "explain": Skill(
        name="explain",
        description="Explain code or concepts in detail",
        allowed_tools=["read_file", "explore_directory", "grep_search"],
        argument_hint="<path-or-concept>",
        body="Read and analyze the specified code or concept. Provide a thorough explanation covering what it does, how it works, and why certain approaches were used.",
    ),
    "translate": Skill(
        name="translate",
        description="Translate code between programming languages",
        allowed_tools=["read_file", "write_file", "edit_file"],
        argument_hint="<source-file> <target-language>",
        body="Translate the given source file to the target programming language. Preserve logic, behavior, and performance characteristics while adapting to target language idioms.",
    ),
    "generate-code": Skill(
        name="generate-code",
        description="Generate code from specification",
        allowed_tools=["read_file", "write_file", "edit_file", "explore_directory"],
        argument_hint="<specification>",
        body="Generate production-ready code based on the given specification. Include error handling, input validation, documentation, and tests.",
    ),
    "search-code": Skill(
        name="search-code",
        description="Search codebase for patterns",
        allowed_tools=["grep_search", "explore_directory", "read_file"],
        argument_hint="<pattern>",
        body="Search the codebase for the specified pattern, function name, or code structure. Report locations, context, and usage patterns.",
    ),
    "analyze-code": Skill(
        name="analyze-code",
        description="Analyze code quality and structure",
        allowed_tools=["read_file", "explore_directory", "grep_search", "run_command"],
        argument_hint="<path>",
        body="Perform comprehensive code analysis including complexity metrics, dependency analysis, code smells, and adherence to best practices.",
    ),
    "visualize": Skill(
        name="visualize",
        description="Generate visualizations of code or data",
        allowed_tools=["read_file", "write_file", "run_command", "explore_directory"],
        argument_hint="<path-or-data>",
        body="Create visual representations of code structure (dependency graphs, call graphs) or data (charts, plots). Output as image files or interactive HTML.",
    ),
    "scaffold": Skill(
        name="scaffold",
        description="Scaffold new project structure",
        allowed_tools=["write_file", "explore_directory", "run_command"],
        argument_hint="<project-name> <type>",
        body="Generate a complete project scaffold with directory structure, config files, entry points, tests, and documentation for the specified project type.",
    ),
    "migrate": Skill(
        name="migrate",
        description="Migrate code between frameworks or versions",
        allowed_tools=["read_file", "write_file", "edit_file", "explore_directory", "run_command", "internet_search"],
        argument_hint="<source> <target>",
        body="Migrate code from one framework, library version, or language version to another. Handle breaking changes, deprecated APIs, and updated patterns.",
    ),
    "validate": Skill(
        name="validate",
        description="Validate code against rules or schemas",
        allowed_tools=["read_file", "run_command", "grep_search"],
        argument_hint="<path> <rules>",
        body="Validate the specified code against defined rules, schemas, or linting standards. Report all violations with locations and suggested fixes.",
    ),
    "format": Skill(
        name="format",
        description="Format code according to style standards",
        allowed_tools=["read_file", "edit_file", "run_command"],
        argument_hint="<path> [style]",
        body="Format the specified files according to the configured or requested style guide. Use auto-formatters and manual adjustments as needed.",
    ),
    "lint": Skill(
        name="lint",
        description="Lint code and report issues",
        allowed_tools=["run_command", "read_file", "edit_file"],
        argument_hint="<path>",
        body="Run linters on the specified codebase and report all issues. Categorize by severity and provide actionable fix suggestions.",
    ),
    "commit-message": Skill(
        name="commit-message",
        description="Generate conventional commit messages",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<scope>",
        body="Analyze the current git diff and generate a conventional commit message following the Conventional Commits specification.",
    ),
    "release": Skill(
        name="release",
        description="Create a new release with changelog",
        allowed_tools=["run_command", "read_file", "write_file"],
        argument_hint="<version>",
        body="Prepare a new release: update version numbers, generate changelog, create git tag, and optionally publish to package registry.",
    ),
    "encrypt-files": Skill(
        name="encrypt-files",
        description="Encrypt or decrypt files for security",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<path> [action]",
        body="Encrypt or decrypt the specified files using strong encryption. Verify integrity of encrypted files.",
    ),
    "backup": Skill(
        name="backup",
        description="Backup project or data",
        allowed_tools=["run_command", "read_file", "explore_directory"],
        argument_hint="<path> [destination]",
        body="Create a timestamped backup of the specified directory or data. Support archive creation, incremental backups, and remote storage.",
    ),
    "monitor-system": Skill(
        name="monitor-system",
        description="Monitor system resources and performance",
        allowed_tools=["run_command"],
        argument_hint="[interval]",
        body="Monitor system resources including CPU, memory, disk, and network. Report current usage and detect anomalies.",
    ),
    "benchmark": Skill(
        name="benchmark",
        description="Benchmark code performance",
        allowed_tools=["read_file", "write_file", "run_command"],
        argument_hint="<path> [iterations]",
        body="Benchmark the specified code or module. Measure execution time, memory usage, and throughput. Generate a comparison report.",
    ),
    "profile": Skill(
        name="profile",
        description="Profile code execution",
        allowed_tools=["run_command", "read_file", "write_file"],
        argument_hint="<script>",
        body="Profile the specified script or module using cProfile or similar tools. Identify hot spots and optimization opportunities.",
    ),
    "containerize": Skill(
        name="containerize",
        description="Create Docker container for project",
        allowed_tools=["read_file", "write_file", "run_command"],
        argument_hint="<path>",
        body="Analyze the project and create appropriate Dockerfile and docker-compose configuration. Optimize for build speed and image size.",
    ),
    "manage-db": Skill(
        name="manage-db",
        description="Manage database operations",
        allowed_tools=["run_command", "read_file", "write_file"],
        argument_hint="<operation> [params]",
        body="Execute database operations including querying, schema inspection, backups, and migrations. Support SQL and NoSQL databases.",
    ),
    "crawl-web": Skill(
        name="crawl-web",
        description="Crawl and extract web content",
        allowed_tools=["run_command", "write_file", "internet_search"],
        argument_hint="<url> [depth]",
        body="Crawl the specified URL and extract content. Support depth-limited crawling, content filtering, and structured output.",
    ),
    "pipeline-create": Skill(
        name="pipeline-create",
        description="Create data processing pipeline",
        allowed_tools=["read_file", "write_file", "run_command"],
        argument_hint="<specification>",
        body="Design and create a data processing pipeline with defined stages, transformations, and outputs. Include error handling and monitoring.",
    ),
    "workflow-run": Skill(
        name="workflow-run",
        description="Run a multi-step workflow",
        allowed_tools=["read_file", "write_file", "run_command", "explore_directory"],
        argument_hint="<workflow-name>",
        body="Execute the specified multi-step workflow. Manage dependencies between steps, handle retries, and report progress.",
    ),
    "report-gen": Skill(
        name="report-gen",
        description="Generate comprehensive reports",
        allowed_tools=["read_file", "write_file", "run_command", "explore_directory"],
        argument_hint="<topic> [format]",
        body="Generate a comprehensive report on the specified topic. Include data analysis, visualizations, and actionable recommendations.",
    ),
    "test-coverage": Skill(
        name="test-coverage",
        description="Analyze and improve test coverage",
        allowed_tools=["run_command", "read_file", "explore_directory"],
        argument_hint="<path>",
        body="Analyze test coverage for the specified codebase. Identify untested functions and suggest test cases to improve coverage.",
    ),
    "dependency-check": Skill(
        name="dependency-check",
        description="Check dependencies for vulnerabilities",
        allowed_tools=["run_command", "read_file", "internet_search"],
        argument_hint="<path>",
        body="Scan project dependencies for known vulnerabilities. Check against CVE databases and suggest updates or mitigations.",
    ),
    "api-test": Skill(
        name="api-test",
        description="Test API endpoints",
        allowed_tools=["run_command", "write_file", "read_file"],
        argument_hint="<spec-or-url>",
        body="Test API endpoints defined in the specification. Validate responses, status codes, schemas, and performance.",
    ),
    "load-test": Skill(
        name="load-test",
        description="Perform load testing",
        allowed_tools=["run_command", "write_file", "read_file"],
        argument_hint="<target> [users]",
        body="Execute load tests against the specified target. Measure response times, throughput, and error rates under load.",
    ),
    "security-scan": Skill(
        name="security-scan",
        description="Scan codebase for security issues",
        allowed_tools=["run_command", "read_file", "grep_search", "explore_directory"],
        argument_hint="<path>",
        body="Scan the codebase for security vulnerabilities using SAST tools and manual analysis. Report findings with severity ratings.",
    ),
    "secret-scan": Skill(
        name="secret-scan",
        description="Scan for hardcoded secrets",
        allowed_tools=["grep_search", "read_file", "explore_directory"],
        argument_hint="<path>",
        body="Scan the codebase for hardcoded secrets, API keys, passwords, and tokens. Report locations and suggest remediation.",
    ),
    "compliance-check": Skill(
        name="compliance-check",
        description="Check code for compliance standards",
        allowed_tools=["read_file", "grep_search", "explore_directory", "internet_search"],
        argument_hint="<path> [standard]",
        body="Check the codebase against specified compliance standards (GDPR, HIPAA, PCI-DSS, SOC2). Report violations and remediation steps.",
    ),
    "docker-build": Skill(
        name="docker-build",
        description="Build Docker images",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<path> [tag]",
        body="Build Docker images for the project. Optimize build layers, apply best practices, and tag appropriately.",
    ),
    "k8s-deploy": Skill(
        name="k8s-deploy",
        description="Deploy to Kubernetes",
        allowed_tools=["read_file", "write_file", "run_command"],
        argument_hint="<manifest>",
        body="Generate and apply Kubernetes manifests. Support deployments, services, configmaps, secrets, and ingress configuration.",
    ),
    "terraform-plan": Skill(
        name="terraform-plan",
        description="Plan Terraform infrastructure",
        allowed_tools=["run_command", "read_file", "write_file"],
        argument_hint="<path>",
        body="Analyze and plan Terraform infrastructure changes. Review state files, plan outputs, and suggest improvements.",
    ),
    "git-flow": Skill(
        name="git-flow",
        description="Manage git workflow",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<action> [params]",
        body="Manage git workflow operations including branch management, merging, rebasing, and conflict resolution following Git Flow conventions.",
    ),
    "merge-strategy": Skill(
        name="merge-strategy",
        description="Determine and execute merge strategy",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<source> <target>",
        body="Analyze branches and determine the best merge strategy. Handle conflicts, suggest squash or rebase options, and execute the merge.",
    ),
    "diff-review": Skill(
        name="diff-review",
        description="Review code diffs in detail",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<ref>",
        body="Review the code diff between the specified references. Analyze each change for correctness, style, and potential issues.",
    ),
    "dependency-update": Skill(
        name="dependency-update",
        description="Update project dependencies",
        allowed_tools=["run_command", "read_file", "edit_file"],
        argument_hint="<path>",
        body="Analyze and update project dependencies to their latest compatible versions. Check for breaking changes and update code accordingly.",
    ),
    "changelog-gen": Skill(
        name="changelog-gen",
        description="Generate changelog from git history",
        allowed_tools=["run_command", "write_file", "read_file"],
        argument_hint="[from-ref] [to-ref]",
        body="Generate a changelog from git commit history between the specified references. Categorize changes by type.",
    ),
    "performance-audit": Skill(
        name="performance-audit",
        description="Audit application performance",
        allowed_tools=["run_command", "read_file", "explore_directory"],
        argument_hint="<path>",
        body="Audit the application for performance issues. Analyze request handling, database queries, caching, and resource utilization.",
    ),
    "accessibility-check": Skill(
        name="accessibility-check",
        description="Check web accessibility",
        allowed_tools=["run_command", "read_file"],
        argument_hint="<path-or-url>",
        body="Check web content for accessibility compliance with WCAG guidelines. Report issues with severity and remediation suggestions.",
    ),
    "schema-gen": Skill(
        name="schema-gen",
        description="Generate data schemas",
        allowed_tools=["read_file", "write_file", "explore_directory"],
        argument_hint="<source> [format]",
        body="Generate data schemas from existing code, databases, or specifications. Support JSON Schema, Avro, Protobuf, and OpenAPI formats.",
    ),
    "mock-gen": Skill(
        name="mock-gen",
        description="Generate mock data and services",
        allowed_tools=["read_file", "write_file", "run_command"],
        argument_hint="<schema> [count]",
        body="Generate realistic mock data or mock API services based on the given schema or specification. Support various output formats.",
    ),
    "integration-test": Skill(
        name="integration-test",
        description="Run integration tests",
        allowed_tools=["run_command", "read_file", "write_file"],
        argument_hint="<path>",
        body="Set up and execute integration tests. Configure test environments, manage test data, and report results.",
    ),
}


class SkillManager:
    def __init__(self, skills_dir: str = ""):
        self.skills_dir = skills_dir
        self.skills = {}
        self._load_bundled()
        if skills_dir and os.path.isdir(skills_dir):
            self._load_from_dir()

    def _load_bundled(self):
        for name, skill in BUNDLED_SKILLS.items():
            self.skills[name] = skill

    def _load_from_dir(self):
        for fname in os.listdir(self.skills_dir):
            if fname.endswith(".md") or fname.endswith(".yaml"):
                fpath = os.path.join(self.skills_dir, fname)
                try:
                    with open(fpath) as f:
                        content = f.read()
                    skill = self._parse_skill_file(content, fname)
                    if skill:
                        self.skills[skill.name] = skill
                except Exception:
                    pass

    def _parse_skill_file(self, content: str, fname: str) -> Skill:
        name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        tools_match = re.search(r"^allowed-tools:\s*\[(.*)\]$", content, re.MULTILINE)
        hint_match = re.search(r"^argument-hint:\s*(.+)$", content, re.MULTILINE)
        body_start = content.find("---", content.find("---") + 1) if content.startswith("---") else -1
        body = content[body_start + 3:].strip() if body_start >= 0 else content
        name = name_match.group(1).strip() if name_match else fname.replace(".md", "").replace(".yaml", "")
        description = desc_match.group(1).strip() if desc_match else ""
        tools_str = tools_match.group(1).strip() if tools_match else ""
        allowed_tools = [t.strip().strip('"').strip("'") for t in tools_str.split(",")] if tools_str else []
        hint = hint_match.group(1).strip() if hint_match else ""
        return Skill(name=name, description=description, allowed_tools=allowed_tools, argument_hint=hint, body=body)

    def list_skills(self) -> list:
        return [{"name": s.name, "description": s.description, "argument_hint": s.argument_hint} for s in self.skills.values()]

    def get_skill(self, name: str) -> Skill:
        return self.skills.get(name)

    def run_skill(self, name: str) -> bool:
        return name in self.skills

    def get_prompt(self, name: str, args: str = "") -> str:
        skill = self.skills.get(name)
        if not skill:
            return ""
        prompt = f"[Skill: {skill.name}]\n{skill.body}"
        if args:
            prompt += f"\n\nContext: {args}"
        if skill.allowed_tools:
            prompt += f"\n\nAllowed tools: {', '.join(skill.allowed_tools)}"
        return prompt