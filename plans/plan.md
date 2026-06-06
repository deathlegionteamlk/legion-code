# Legion Code — Massive Expansion + GitHub Upload + Code Protection

## Goal
Expand Legion Code with 20+ new features (deep skills, advanced tools, workflow engine, code protection, GitHub sync, auto-documentation, etc.), then upload to GitHub with full code protection via PyArmor obfuscation.

## Research Summary
- **PyArmor** (dashingsoft/pyarmor) is the industry-standard Python obfuscator — obfuscates bytecode, constants, strings, binds to machines. Used by production teams. Installed via `pip install pyarmor`
- **GitHub REST API** with PAT: use `Authorization: Bearer ghp_...` header or `PyGithub` library for repo creation and push
- **Multi-provider agents** gaining traction (ClawCodex, OpenRouter ecosystem) — confirmed pattern
- Additional skills are a proven concept (Anthropic Agent Skills, Oct 2025)

## Subtasks

1. **Create `legion/skills.py` — MASSIVE skill expansion to 50+ skills**
   - Add 50+ new bundled skills: refactor, debug, optimize, document, deploy, architect, explain, translate, generate-code, search-code, analyze-code, visualize, scaffold, migrate, validate, format, lint, commit-message, release, encrypt-files, backup, monitor-system, benchmark, profile, containerize, manage-db, crawl-web, pipeline-create, workflow-run, report-gen, test-coverage, dependency-check, api-test, load-test, security-scan, secret-scan, compliance-check, docker-build, k8s-deploy, terraform-plan, git-flow, merge-strategy, diff-review, dependency-update, changelog-gen, performance-audit, accessibility-check, schema-gen, mock-gen, integration-test
   - Each skill has: name, description, allowed_tools, argument_hint, body with detailed instructions
   - Keep `Skill` dataclass, `BUNDLED_SKILLS`, `SkillManager` structure

2. **Create `legion/encryption.py` — AES encryption for code protection**
   - AES-CBC encryption/decryption using PyCryptodome
   - EncryptFile class: generate_key(), encrypt_file(), decrypt_file()
   - Encrypt sessions, configs, and arbitrary files
   - Key management with hashing of user passphrase

3. **Create `legion/obfuscator.py` — PyArmor wrapper for full code protection**
   - `protect_all()` function: runs pyarmor on all legion/*.py files
   - `protect_file(path)` individual file protection
   - Runtime decryption helper
   - License key binding support
   - Build output to `dist/` directory

4. **Create `legion/github_sync.py` — GitHub integration with PAT auth**
   - `GithubSync` class: create_repo(), push_code(), pull_latest(), backup_repo()
   - Uses PyGithub library with Personal Access Token
   - File filtering: only specified files (include/exclude patterns)
   - Auto README.md generation for pushed repos
   - Branch management, tag releases

5. **Create `legion/workflow.py` — Multi-step workflow engine**
   - `Workflow` class with DAG-based step execution
   - `WorkflowStep` dataclass: id, description, action (tool_call), depends_on, condition, retry_policy
   - Sequential and parallel execution
   - State persistence between steps
   - Conditional branching (if/else steps)
   - Retry with backoff per step
   - Workflow validation (cycle detection)

6. **Create `legion/context_engine.py` — Smart context management**
   - `ContextEngine` class: token budget tracking, message pruning strategies
   - Summarization-based pruning
   - Sliding window with importance scoring
   - Priority-based retention (system msgs always kept)
   - `summarize_to_fit(budget)` method
   - Token counting utility

7. **Create `legion/code_analyzers.py` — AST-based code analysis**
   - `CodeAnalyzer` class: analyze complexity (cyclomatic, cognitive)
   - Dependency graph extraction from imports
   - Function/class extraction and documentation
   - Code quality scoring
   - Dead code detection
   - Test coverage mapping (find untested functions)

8. **Create `legion/auto_documenter.py` — Auto-document codebases**
   - `AutoDocumenter` class: scan project, extract docstrings, generate docs
   - Output formats: Markdown, HTML, PDF (via reportlab or markdown)
   - API reference generation
   - README.md auto-gen
   - CHANGELOG.md auto-gen from git history

9. **Create `legion/benchmark.py` — Model and system benchmarking**
   - `Benchmark` class: test model latency, throughput, quality
   - Tool execution speed benchmarking
   - Report generation with rich tables and charts
   - Compare multiple models on same task

10. **Create `legion/deployment.py` — Deploy agents/apps**
    - `Deployer` class: Docker build/push, docker-compose setup
    - cloud deployment (render, railway, fly.io config generators)
    - systemd service file generator for background agents

11. **Create `legion/tools/database_tools.py` — Database tools**
    - `db_query()` — Execute SQL queries (SQLite, PostgreSQL via config)
    - `db_schema()` — Show database schema
    - `db_backup()` — Backup database
    - `db_migrate()` — Run migrations
    - `redis_query()` — Redis operations

12. **Create `legion/tools/network_tools.py` — Network/HTTP tools**
    - `http_request()` — Full HTTP client (GET, POST, PUT, DELETE)
    - `ping_test()` — Network connectivity test
    - `dns_lookup()` — DNS resolution
    - `port_scan()` — TCP port scanning
    - `api_discover()` — API endpoint discovery from OpenAPI/Swagger

13. **Create `legion/tools/file_advanced.py` — Advanced file tools**
    - `file_diff()` — Show diff between two files
    - `file_merge()` — Merge two files with conflict markers
    - `batch_rename()` — Pattern-based batch rename
    - `file_stat()` — Detailed file statistics
    - `watch_directory()` — Watch directory for changes
    - `file_find_duplicates()` — Find duplicate files by hash
    - `archive_extract()` — Extract zip/tar archives
    - `archive_create()` — Create zip/tar archives

14. **Create `legion/prompt_engineer.py` — Prompt engineering toolkit**
    - `PromptOptimizer` class: test prompt variations, score quality
    - `PromptTemplate` class: reusable templates with variables
    - `PromptLibrary` class: store/retrieve prompts by tag
    - A/B testing of prompts
    - Token optimization (shorten prompts while preserving meaning)

15. **Create `legion/tools/ai_tools.py` — AI/ML utility tools**
    - `embed_text()` — Generate embeddings
    - `classify_text()` — Zero-shot classification
    - `extract_entities()` — NER extraction
    - `summarize_text()` — Text summarization
    - `translate_text()` — Translation
    - `generate_image()` — Image generation via API

16. **Update `legion/tools/__init__.py`** — Register all new tools (database, network, file_advanced, ai_tools)
    - Import and register all new tool definitions

17. **Update `legion/config.py`** — Add new config fields
    - `github_token`, `github_repo`, `encryption_key`, `obfuscate_on_build`, `deploy_target`, `database_url`, `workflow_dir`, `benchmark_enabled`, `context_budget`

18. **Update `legion/commands.py`** — Add new slash commands for new features
    - `/github create|push|pull` — GitHub commands
    - `/encrypt <file>` — Encrypt file
    - `/obfuscate` — Obfuscate codebase
    - `/workflow run <name>` — Run workflow
    - `/benchmark <model>` — Benchmark model
    - `/deploy <target>` — Deploy agent
    - `/docs generate` — Generate documentation
    - `/context show|trim` — Context management
    - `/analyze <path>` — Code analysis
    - `/db query|schema` — Database operations
    - `/prompt test|optimize` — Prompt engineering

19. **Update `run.py`** — Integrate all new features
    - Import all new modules in CLI
    - Setup functions for new components
    - Enhanced interactive mode with new commands
    - Handle new CLI flags (--github, --encrypt, --obfuscate, --deploy, --docs, --benchmark)
    - GitHub push on build flag (`--github-push`)
    - Auto-obfuscation on `--protect` flag

20. **Install pyarmor, pycryptodome, PyGithub, reportlab** for new modules

21. **Run PyArmor obfuscation** on all legion/*.py files to protect the codebase

22. **Create GitHub repo and push code** using the provided token (set via GITHUB_TOKEN env var)
    - Create repo named `legion-code` (or use existing)
    - Push ALL files (the full project)
    - Note: obfuscated files go into dist/ — push both original and obfuscated

23. **Run comprehensive tests** — all modules import, all tools registered, CLI works

## Deliverables
- 15 new modules in legion/ (skills expanded, encryption, obfuscator, github_sync, workflow, context_engine, code_analyzers, auto_documenter, benchmark, deployment, tools/database_tools, tools/network_tools, tools/file_advanced, prompt_engineer, tools/ai_tools)
- All updated existing files
- Obfuscated code in dist/
- GitHub repo pushed with all code
- All tests passing

## Evaluation Criteria
- All modules import cleanly
- PyArmor obfuscation succeeds on all .py files
- GitHub repo created and pushed successfully
- New slash commands functional
- All tests pass

## Notes
- GitHub token: set via GITHUB_TOKEN environment variable
- Zero comments on all code
- All imports use absolute paths from project root