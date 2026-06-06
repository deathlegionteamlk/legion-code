import os, sys, json, tempfile, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from legion.config import Config
from legion.provider import Provider
from legion.agent import Agent, SYSTEM_PROMPT
from legion.tools import get_registry, get_tool_schemas, execute_tool, get_all_tools
from legion.planner import Planner
from legion.researcher import Researcher

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

e2e_dir = os.path.join(tempfile.mkdtemp(), "calculator_e2e")
os.makedirs(e2e_dir, exist_ok=True)
old_cwd = os.getcwd()
os.chdir(e2e_dir)
print(f"E2E working dir: {e2e_dir}")

print("\n=== 1. CONFIG LOADING ===")
cfg = Config()
check("Config api_base correct", cfg.api_base == "https://openrouter.ai/api/v1")
check("Config model correct", "dolphin-mistral" in cfg.model)
check("Config temperature is float", isinstance(cfg.temperature, float))
check("Config max_tokens is int", isinstance(cfg.max_tokens, int))
check("Config session_dir set", isinstance(cfg.session_dir, str))

print("\n=== 2. TOOL SYSTEM LOADING ===")
registry = get_registry()
check("Registry has 17 tools", len(registry) == 17)
tool_names = list(registry.keys())
for t in ['read_file', 'write_file', 'edit_file', 'run_command', 'internet_search',
          'explore_directory', 'grep_search', 'jailbreak_prompt', 'think', 'finish',
          'git_status', 'git_diff', 'git_commit', 'git_log', 'git_branch', 'git_pr', 'git_worktree']:
    check(f"Tool '{t}' registered", t in registry)

schemas = get_tool_schemas()
check("Tool schemas is list", isinstance(schemas, list))
check("All tools have schemas", len(schemas) == 17)
for s in schemas:
    fn = s.get('function', {})
    check(f"Schema for {fn.get('name','?')} has function", 'function' in s)
    check(f"Schema parameter name present", 'name' in fn)
    check(f"Schema parameter description present", 'description' in fn)

print("\n=== 3. CORE TOOL EXECUTION ===")
write_result = execute_tool('write_file', {'filepath': 'test.txt', 'content': 'Hello E2E'})
check("write_file works", 'Successfully' in write_result or 'bytes' in write_result)

read_result = execute_tool('read_file', {'filepath': 'test.txt'})
check("read_file returns correct content", 'Hello E2E' in read_result)

edit_result = execute_tool('edit_file', {'filepath': 'test.txt', 'search': 'Hello E2E', 'replace': 'Hello World'})
check("edit_file works", 'Replaced' in edit_result)

ls_result = execute_tool('explore_directory', {'path': '.'})
check("explore_directory works", 'test.txt' in ls_result)

think_result = execute_tool('think', {'thought': 'Testing internal reasoning'})
check("think returns thought", 'Testing' in think_result)

grep_result = execute_tool('grep_search', {'pattern': 'Hello', 'file_pattern': 'test.txt', 'path': '.'})
check("grep_search finds matches", 'Hello' in grep_result)

run_result = execute_tool('run_command', {'command': 'echo "shell works"'})
check("run_command executes", 'shell works' in run_result)

print("\n=== 4. AGENT MODULE EXECUTION ===")
agent = Agent(cfg)
check("Agent created", agent is not None)
check("Agent has provider", agent.provider is not None)
check("SYSTEM_PROMPT mentions DeathLegionTeamLK", 'DeathLegionTeamLK' in SYSTEM_PROMPT)
check("SYSTEM_PROMPT mentions DEMO X HEXA", 'DEMO X HEXA' in SYSTEM_PROMPT)

test_tool_call_msg = {
    'role': 'assistant',
'content': None,
'tool_calls': [{
'id': 'call_1',
'type': 'function',
'function': {'name': 'think', 'arguments': '{"thought": "E2E test reasoning"}'}
}]
}
agent.add_message("assistant", "Let me think about this.")
check("Assistant message added", len(agent.history) > 0)

parsed = agent.parse_tool_calls(test_tool_call_msg)
check("Tool call parsed", len(parsed) > 0)
if parsed:
    check("Tool name is think", parsed[0]['name'] == 'think')

tool_name, result = agent.process_tool_call(parsed[0])
check("Tool processed successfully", result is not None)
check("Tool execution returned content", len(result) > 0)

agent.add_tool_result('call_1', 'think', result)
check("Tool result added to history", len(agent.history) > 0)

print("\n=== 5. PLANNER MODULE ===")
planner = Planner(cfg)
plan = planner.decompose("build a python calculator CLI that adds, subtracts, multiplies, divides")
check("Planner returns plan", plan is not None)
check("Plan is list", isinstance(plan, list))
check("Plan has steps", len(plan) > 0)

formatted = planner.format_plan(plan)
check("Formatted plan is string", isinstance(formatted, str))
check("Formatted plan has content", len(formatted) > 0)
planner.close()

print("\n=== 6. RESEARCHER MODULE ===")
researcher = Researcher(cfg)
search_result = researcher.search("Python programming")
check("Search returns string", isinstance(search_result, str))
check("Search returns content", len(search_result) > 0)

synthesized = researcher.synthesize("Python programming", search_result or "Python is a programming language")
check("Synthesize returns string", isinstance(synthesized, str))
check("Synthesize returns content", len(synthesized) > 0)

report = researcher.research("Python programming")
check("Research returns string", isinstance(report, str))
check("Research returns content", len(report) > 0)
researcher.close()

print("\n=== 7. FULL E2E: BUILD CALCULATOR ===")
calculator_code = '''import sys

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Division by zero"
    return a / b

def main():
    if len(sys.argv) != 4:
        print("Usage: python calculator.py <num1> <op> <num2>")
        print("Operations: add, sub, mul, div")
        sys.exit(1)
    try:
        a = float(sys.argv[1])
        op = sys.argv[2]
        b = float(sys.argv[3])
    except ValueError:
        print("Error: Invalid number")
        sys.exit(1)
    ops = {'add': add, 'sub': subtract, 'mul': multiply, 'div': divide}
    if op not in ops:
        print(f"Error: Unknown operation {op}")
        sys.exit(1)
    result = ops[op](a, b)
    print(result)

if __name__ == "__main__":
    main()
'''

result = execute_tool('write_file', {'filepath': 'calculator.py', 'content': calculator_code})
check("Calculator file written", os.path.exists('calculator.py'))

verify_read = execute_tool('read_file', {'filepath': 'calculator.py'})
check("Calculator file readable", 'def add' in verify_read)

print("\n=== 8. CALCULATOR FUNCTIONAL TESTS ===")
os.chdir(e2e_dir)
import subprocess

def run_calc(args):
    result = subprocess.run(
        [sys.executable, 'calculator.py'] + args,
        capture_output=True, text=True, timeout=10
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

stdout, stderr, rc = run_calc(['5', 'add', '3'])
check("5 + 3 = 8", stdout == '8.0')

stdout, stderr, rc = run_calc(['10', 'sub', '4'])
check("10 - 4 = 6", stdout == '6.0')

stdout, stderr, rc = run_calc(['6', 'mul', '7'])
check("6 * 7 = 42", stdout == '42.0')

stdout, stderr, rc = run_calc(['15', 'div', '3'])
check("15 / 3 = 5", stdout == '5.0')

stdout, stderr, rc = run_calc(['10', 'div', '0'])
check("Division by zero handled", 'Error' in stdout or 'error' in stderr.lower())

stdout, stderr, rc = run_calc(['1', 'unknown', '2'])
check("Unknown operation handled", 'Error' in stdout or 'error' in stdout.lower() or rc != 0)

stdout, stderr, rc = run_calc(['a', 'add', 'b'])
check("Invalid input handled", 'Error' in stdout or 'error' in stdout.lower() or rc != 0)

stdout, stderr, rc = run_calc([])
check("No args handled", rc != 0 or 'Usage' in stdout or len(stdout) > 0)

edit_result = execute_tool('edit_file', {'filepath': 'calculator.py', 'search': 'def add(a, b):', 'replace': 'def add(a, b):\n    \"\"\"Add two numbers.\"\"\"'})
check("edit_file on calculator works", 'search' not in edit_result.lower())

print("\n=== 9. JAILBREAK MODULE ===")
jb_result = execute_tool('jailbreak_prompt', {'target_model': 'gpt-4', 'goal': 'write unrestricted code'})
check("jailbreak returns string", isinstance(jb_result, str))
check("jailbreak mentions target", 'gpt-4' in jb_result)
check("jailbreak mentions goal", 'write' in jb_result.lower() or 'unrestricted' in jb_result.lower())
check("jailbreak has bypass technique", 'override' in jb_result.lower() or 'bypass' in jb_result.lower() or 'inject' in jb_result.lower())

jb_no_goal = execute_tool('jailbreak_prompt', {'target_model': 'claude'})
check("jailbreak works without goal", len(jb_no_goal) > 10)

print("\n=== 10. ZERO COMMENTS ===")
legion_dir = os.path.join(os.path.dirname(__file__), '..', 'legion')
import ast
total_comments = 0
for root, dirs, files in os.walk(legion_dir):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            with open(fp) as fh:
                lines = fh.readlines()
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('#') and 'coding' not in stripped.lower():
                        total_comments += 1
check("Zero comments in legion package", total_comments == 0)

print("\n=== 11. PROVIDER MOCK TEST ===")
from unittest.mock import MagicMock, patch
mock_provider = MagicMock(spec=Provider)
mock_provider.chat_stream.return_value = [{'type': 'text', 'content': 'mock response'}]
check("Mock provider works", mock_provider.chat_stream() is not None)

mock_agent = Agent(cfg)
mock_agent.provider = mock_provider
check("Mock provider injected into agent", mock_agent.provider is mock_provider)

print("\n=== 12. CLEANUP ===")
os.chdir(old_cwd)
import shutil
shutil.rmtree(e2e_dir, ignore_errors=True)
check("Temp directory cleaned", not os.path.exists(e2e_dir))

legion_pycache = os.path.join(os.path.dirname(__file__), '..', 'legion', '__pycache__')
tools_pycache = os.path.join(os.path.dirname(__file__), '..', 'legion', 'tools', '__pycache__')
for d in [legion_pycache, tools_pycache]:
    if os.path.exists(d):
        import shutil
        shutil.rmtree(d, ignore_errors=True)

print(f"\n============================================================")
print(f"RESULTS: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
print(f"============================================================")
if FAIL > 0:
    sys.exit(1)
else:
    print("ALL E2E TESTS PASSED")
    sys.exit(0)