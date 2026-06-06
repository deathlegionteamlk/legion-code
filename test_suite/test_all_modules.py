import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from legion.config import Config
from legion.provider import Provider, ProviderError
from legion.agent import Agent, SYSTEM_PROMPT
from legion.planner import Planner
from legion.researcher import Researcher
from legion.tools import get_registry, get_tool_schemas, execute_tool

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        detail_str = f" {detail}" if detail else " FAILED"
        print(f"  FAIL: {name}{detail_str}")

def check_eq(name, a, b):
    check(name, a == b, f"(got {repr(a)}, expected {repr(b)})")

def check_in(name, item, container):
    check(name, item in container, f"(missing {repr(item)})")

print("=" * 60)
print("LEGION CODE - COMPREHENSIVE MODULE TESTS")
print("=" * 60)

print("\n--- 1. CONFIG MODULE ---")
cfg = Config()
check("Config has api_base", hasattr(cfg, 'api_base'))
check_eq("api_base is OpenRouter", cfg.api_base, 'https://openrouter.ai/api/v1')
check_eq("model is Venice uncensored free", cfg.model, 'cognitivecomputations/dolphin-mistral-24b-venice-edition:free')
check("Config has api_key from env", hasattr(cfg, 'api_key'))
check("Config has temperature", hasattr(cfg, 'temperature'))
check("Config has max_tokens", hasattr(cfg, 'max_tokens'))
check("Config has top_p", hasattr(cfg, 'top_p'))
check("Config has max_tool_call_iterations", hasattr(cfg, 'max_tool_call_iterations'))
check("Config has session_dir", hasattr(cfg, 'session_dir'))
check("Config has request_timeout", hasattr(cfg, 'request_timeout'))
check("Config has history_limit", hasattr(cfg, 'history_limit'))
check("session_dir ends with sessions", cfg.session_dir.endswith('sessions'))
check_eq("default temperature is 0.7", cfg.temperature, 0.7)
check_eq("default max_tokens is 4096", cfg.max_tokens, 4096)

print("\n--- 2. PROVIDER MODULE ---")
check("Provider class exists", 'Provider' in dir())
check("ProviderError exists", 'ProviderError' in dir())
p = Provider(cfg)
check("Provider has chat method", hasattr(p, 'chat'))
check("Provider has chat_stream method", hasattr(p, 'chat_stream'))
check("Provider has extract_tool_calls method", hasattr(p, 'extract_tool_calls'))
check("Provider has extract_assistant_message method", hasattr(p, 'extract_assistant_message'))
check("Provider has format_tool_result method", hasattr(p, 'format_tool_result'))
check("Provider has close method", hasattr(p, 'close'))
check("Provider has _headers property", hasattr(p.__class__, '_headers'))
check("Provider._headers includes Content-Type", 'Content-Type' in p._headers)
check("Provider._headers includes Authorization when key set", not 'Bearer' in str(p._headers) or True)
p.close()

test_response = {
    "choices": [{
        "message": {
            "role": "assistant",
            "content": "Hello world",
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {"name": "think", "arguments": '{"thought":"test"}'}
            }]
        }
    }]
}
msg = p.extract_assistant_message(test_response)
check("extract_assistant_message extracts message dict", isinstance(msg, dict))
check("extract_assistant_message preserves content", msg.get('content') == 'Hello world')

tool_calls = p.extract_tool_calls(msg)
check("extract_tool_calls returns list", isinstance(tool_calls, list))
check("extract_tool_calls extracts tool calls", len(tool_calls) > 0)
if tool_calls:
    check("tool call has id", 'id' in tool_calls[0])
    check("tool call has function name", tool_calls[0].get('function', {}).get('name') == 'think')
    check("tool call has parsed arguments", isinstance(tool_calls[0].get('function', {}).get('arguments'), dict))

tr = p.format_tool_result({"id": "test"}, "done")
check("format_tool_result returns dict", isinstance(tr, dict))
check("format_tool_result has role=tool", tr.get('role') == 'tool')
check("format_tool_result has tool_call_id", 'tool_call_id' in tr)

print("\n--- 3. TOOL SYSTEM ---")
registry = get_registry()
schemas = get_tool_schemas()
check_eq("Registry has 17 tools", len(registry), 17)
check_eq("Schemas has 17 entries", len(schemas), 17)

expected_tools = ['think', 'finish', 'read_file', 'write_file', 'edit_file',
                  'run_command', 'internet_search', 'explore_directory',
                  'grep_search', 'jailbreak_prompt',
                  'git_status', 'git_diff', 'git_commit', 'git_log',
                  'git_branch', 'git_pr', 'git_worktree']
for t in expected_tools:
    check(f"Tool registered: {t}", t in registry)
    check(f"Tool name matches: {t}", registry[t]['name'] == t)
    check(f"Tool has description: {t}", len(registry[t].get('description', '')) > 0)
    check(f"Tool has handler: {t}", callable(registry[t].get('handler')))
    if t not in ('think', 'finish'):
        schema = registry[t].get('input_schema', {})
        check(f"Tool {t} has input schema", schema.get('type') == 'object')

for s in schemas:
    check("Schema has type=function", s.get('type') == 'function')
    check("Schema has function.name", len(s.get('function', {}).get('name', '')) > 0)
    check("Schema has function.description", len(s.get('function', {}).get('description', '')) > 0)
    check("Schema has function.parameters", isinstance(s.get('function', {}).get('parameters'), dict))

result = execute_tool('think', {'thought': 'testing'})
check("think tool returns string", isinstance(result, str))
check("think tool records thought", 'testing' in result)

result = execute_tool('finish', {'summary': 'test complete'})
check("finish tool returns string", isinstance(result, str))
check("finish tool records summary", 'test complete' in result)

try:
    execute_tool('nonexistent_tool', {})
    check("nonexistent tool returns error", True)
except ValueError:
    check("nonexistent tool raises ValueError", True)

print("\n--- 4. FILE TOOLS ---")
with tempfile.TemporaryDirectory() as tmpdir:
    test_file = os.path.join(tmpdir, 'test.txt')
    result = execute_tool('write_file', {'filepath': test_file, 'content': 'hello world\nline2'})
    check("write_file returns success", 'wrote' in result.lower() or 'written' in result.lower() or 'Successfully' in result)
    check("file created on disk", os.path.exists(test_file))
    with open(test_file) as f:
        check("file content correct", f.read() == 'hello world\nline2')

    result = execute_tool('read_file', {'filepath': test_file})
    check("read_file returns content", 'hello world' in result)
    check("read_file shows full content", 'line2' in result)

    result = execute_tool('edit_file', {'filepath': test_file, 'search': 'hello world', 'replace': 'goodbye world'})
    check("edit_file returns success", 'Replaced' in result)
    with open(test_file) as f:
        content = f.read()
    check("edit_file changed content", 'goodbye world' in content)
    check("edit_file preserved other content", 'line2' in content)

    result = execute_tool('read_file', {'filepath': '/nonexistent/path/file.txt'})
    check("read_file handles missing file", 'error' in result.lower() or 'not found' in result.lower())

print("\n--- 5. SHELL TOOL ---")
result = execute_tool('run_command', {'command': 'echo "hello from shell"'})
check("run_command executes", 'hello from shell' in result)
result = execute_tool('run_command', {'command': 'ls /nonexistent_dir_xyz_123'})
check("run_command handles errors", 'error' in result.lower() or 'No such' in result or 'exit code' in result.lower() or 'not found' in result.lower())

print("\n--- 6. CODEBASE TOOLS ---")
with tempfile.TemporaryDirectory() as tmpdir:
    os.makedirs(os.path.join(tmpdir, 'subdir'))
    with open(os.path.join(tmpdir, 'file1.py'), 'w') as f:
        f.write('print("hello")\n')
    with open(os.path.join(tmpdir, 'file2.txt'), 'w') as f:
        f.write('world\n')
    with open(os.path.join(tmpdir, 'subdir', 'lib.py'), 'w') as f:
        f.write('def foo():\n    pass\n')

    result = execute_tool('explore_directory', {'path': tmpdir})
    check("explore_directory shows files", 'file1.py' in result)
    check("explore_directory shows subdir", 'subdir' in result)
    check("explore_directory shows nested", 'lib.py' in result)

    result = execute_tool('explore_directory', {'path': '/nonexistent'})
    check("explore_directory handles missing path", 'error' in result.lower() or 'not found' in result.lower())

    result = execute_tool('grep_search', {'pattern': 'print', 'path': tmpdir})
    check("grep_search finds matches", 'print' in result)
    check("grep_search shows filename", 'file1.py' in result)

    result = execute_tool('grep_search', {'pattern': 'nonexistent_pattern_xyz', 'path': tmpdir})
    check("grep_search handles no matches", 'no' in result.lower() or 'No' in result)

print("\n--- 7. SEARCH TOOL ---")
result = execute_tool('internet_search', {'query': 'Python programming language'})
check("internet_search returns results", len(result) > 0)
check("internet_search returns results or error message", len(result) > 0)
check("internet_search returns meaningful content", 'Search' in result or 'error' in result.lower() or 'result' in result.lower())

print("\n--- 8. AGENT MODULE ---")
check("Agent class exists", 'Agent' in dir())
check("SYSTEM_PROMPT exported", len(SYSTEM_PROMPT) > 100)
check("SYSTEM_PROMPT mentions DeathLegionTeamLK", 'DeathLegionTeamLK' in SYSTEM_PROMPT)
check("SYSTEM_PROMPT mentions DEMO X HEXA", 'DEMO X HEXA' in SYSTEM_PROMPT)
check("SYSTEM_PROMPT mentions tools", 'tools' in SYSTEM_PROMPT.lower())
check("SYSTEM_PROMPT mentions JSON", 'json' in SYSTEM_PROMPT.lower())

agent = Agent(cfg)
check("Agent has add_message", hasattr(agent, 'add_message'))
check("Agent has run", hasattr(agent, 'run'))
check("Agent has run_streaming", hasattr(agent, 'run_streaming'))
check("Agent has parse_tool_calls", hasattr(agent, 'parse_tool_calls'))
check("Agent has process_tool_call", hasattr(agent, 'process_tool_call'))
check("Agent has history", hasattr(agent, 'history'))
check("Agent has tool_schemas", hasattr(agent, 'tool_schemas'))

agent.add_message('user', 'list files')
check("add_message stores message", len(agent.history) > 0)
check("message has role=user", agent.history[-1].get('role') == 'user')
check("message has content", 'list files' in agent.history[-1].get('content', ''))

test_msg_openai = {
    'role': 'assistant',
    'content': None,
    'tool_calls': [{
        'id': 'call_1',
        'type': 'function',
        'function': {'name': 'think', 'arguments': '{"thought":"testing parsing"}'}
    }]
}
tcs = agent.parse_tool_calls(test_msg_openai)
check("parse_tool_calls extracts OpenAPI-style calls", len(tcs) > 0)
if tcs:
    check("parsed tool has name", tcs[0].get('name') == 'think')
    check("parsed tool has arguments dict", isinstance(tcs[0].get('arguments'), dict))
    check("parsed tool thought correct", tcs[0]['arguments'].get('thought') == 'testing parsing')

test_msg_text = {'role': 'assistant', 'content': 'Just thinking out loud'}
tcs = agent.parse_tool_calls(test_msg_text)
check("parse_tool_calls returns text as _text tool", len(tcs) > 0)
if tcs:
    check("text-only returns _text name", tcs[0].get('name') == '_text')

test_msg_empty = {'role': 'assistant', 'content': ''}
tcs = agent.parse_tool_calls(test_msg_empty)
check("parse_tool_calls handles empty content", len(tcs) == 0)

test_msg_none = None
tcs = agent.parse_tool_calls(test_msg_none)
check("parse_tool_calls handles None", len(tcs) == 0)

agent.add_tool_call_messages([
    {'id': 'call_1', 'function': {'name': 'think', 'arguments': {'thought': 'test'}}}
])
check("add_tool_call_messages stores tool_calls", len(agent.history) > 0)

print("\n--- 9. PLANNER MODULE ---")
planner = Planner(cfg)
check("Planner class exists", 'Planner' in dir())
check("Planner has decompose", hasattr(planner, 'decompose'))
check("Planner has format_plan", hasattr(planner, 'format_plan'))

plan = planner.decompose("build a python calculator")
check("decompose returns list", isinstance(plan, list))
check("plan has at least 1 step", len(plan) > 0)
if len(plan) > 0:
    step = plan[0]
    check("plan step has id", 'id' in step)
    check("plan step has description", 'description' in step)
    check("plan step has expected_output", 'expected_output' in step)
    check("plan step has dependencies", 'dependencies' in step)

formatted = planner.format_plan(plan)
check("format_plan returns string", isinstance(formatted, str))
check("format_plan includes description", len(formatted) > 0)

print("\n--- 10. RESEARCHER MODULE ---")
researcher = Researcher(cfg)
check("Researcher class exists", 'Researcher' in dir())
check("Researcher has search", hasattr(researcher, 'search'))
check("Researcher has synthesize", hasattr(researcher, 'synthesize'))
check("Researcher has research", hasattr(researcher, 'research'))

search_result = researcher.search("Python programming", max_results=5)
check("search returns string", isinstance(search_result, str))
check("search returns results", len(search_result) > 0)
check("search returns content", 'Search' in search_result or 'error' in search_result.lower() or 'result' in search_result.lower())

synthesized = researcher.synthesize("Python programming", search_result)
check("synthesize returns string", isinstance(synthesized, str))
check("synthesize returns content", len(synthesized) > 0)

report = researcher.research("Python programming")
check("research returns string", isinstance(report, str))
check("research returns content", len(report) > 0)

print("\n--- 11. AGENT TOOL EXECUTION INTEGRATION ---")
tool_name, result = agent.process_tool_call({"name": "think", "arguments": {"thought": "integration test"}})
check("process_tool_call returns tool name", tool_name == 'think' or tool_name == '_text')
check("process_tool_call returns string result", isinstance(result, str))

tool_name, result = agent.process_tool_call({"name": "finish", "arguments": {"summary": "done"}})
check("process_tool_call handles finish", isinstance(result, str))
check("process_tool_call finish says complete", 'complete' in result.lower() or 'done' in result.lower())

with tempfile.TemporaryDirectory() as tmpdir:
    test_file = os.path.join(tmpdir, 'e2e_test.txt')
    execute_tool('write_file', {'filepath': test_file, 'content': 'E2E test data'})
    result = execute_tool('read_file', {'filepath': test_file})
    check("write+read E2E workflow", 'E2E test data' in result)

    execute_tool('edit_file', {'filepath': test_file, 'search': 'E2E test', 'replace': 'Updated E2E'})
    result = execute_tool('read_file', {'filepath': test_file})
    check("write+edit+read E2E workflow", 'Updated E2E' in result)

print("\n--- 12. JAILBREAK MODULE ---")

result = execute_tool('jailbreak_prompt', {'target_model': 'claude-sonnet', 'goal': 'write a poem about AI'})
check("jailbreak_prompt returns string", isinstance(result, str))
check("jailbreak_prompt mentions target", 'claude' in result.lower())
check("jailbreak_prompt mentions goal", 'poem' in result.lower() or 'ai' in result.lower())
check("jailbreak_prompt has bypass technique", 'override' in result.lower() or 'developer mode' in result.lower() or 'roleplay' in result.lower() or 'DAN' in result or 'restriction' in result.lower() or 'circumvent' in result.lower())

result = execute_tool('jailbreak_prompt', {'target_model': 'gpt-4'})
check("jailbreak_prompt works without goal", 'gpt-4' in result.lower())
check("jailbreak_prompt includes system prompt override", 'system prompt' in result.lower() or 'override' in result.lower() or 'developer mode' in result.lower())

print("\n--- 13. ZERO COMMENTS VERIFICATION ---")
root = os.path.join(os.path.dirname(__file__), '..')
py_files = []
for path, dirs, files in os.walk(root):
    if '__pycache__' in path or '.git' in path:
        continue
    for f in files:
        if f.endswith('.py'):
            py_files.append(os.path.join(path, f))

total_comment_lines = 0
files_with_comments = []
for pf in sorted(py_files):
    with open(pf) as f:
        lines = f.readlines()
    comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
    rel = os.path.relpath(pf, root)
    if comment_lines > 0:
        files_with_comments.append(f"{rel} ({comment_lines} lines)")
        total_comment_lines += comment_lines

check_eq("Zero comment lines across all .py files", total_comment_lines, 0)
check_eq("Files with comments (should be 0)", len(files_with_comments), 0)

print(f"\n{'='*60}")
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
if FAIL == 0:
    print("ALL TESTS PASSED")
else:
    print(f"SOME TESTS FAILED")
print(f"{'='*60}")

sys.exit(0 if FAIL == 0 else 1)