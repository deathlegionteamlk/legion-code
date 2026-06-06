import os
import json
import time
from datetime import datetime


class SessionStore:
    def __init__(self, session_dir: str):
        self.session_dir = session_dir
        os.makedirs(self.session_dir, exist_ok=True)

    def save(self, session_id: str, data: dict) -> str:
        path = os.path.join(self.session_dir, f"{session_id}.json")
        data["_saved_at"] = datetime.now().isoformat()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def load(self, session_id: str) -> dict:
        path = os.path.join(self.session_dir, f"{session_id}.json")
        if not os.path.exists(path):
            return {}
        with open(path) as f:
            return json.load(f)

    def list_sessions(self) -> list:
        sessions = []
        if not os.path.isdir(self.session_dir):
            return sessions
        for fname in sorted(os.listdir(self.session_dir), reverse=True):
            if fname.endswith(".json"):
                path = os.path.join(self.session_dir, fname)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    sessions.append({
                        "id": fname.replace(".json", ""),
                        "path": path,
                        "saved_at": data.get("_saved_at", ""),
                        "model": data.get("config", {}).get("model", ""),
                        "turn_count": len(data.get("history", [])),
                        "summary": data.get("summary", ""),
                        "filepath": path,
                    })
                except Exception:
                    sessions.append({"id": fname.replace(".json", ""), "path": path, "saved_at": "", "model": "", "turn_count": 0, "summary": "", "filepath": path})
        return sessions

    def get_latest(self) -> dict:
        sessions = self.list_sessions()
        return sessions[0] if sessions else None

    def delete(self, session_id: str) -> bool:
        path = os.path.join(self.session_dir, f"{session_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False


class ProjectContextLoader:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def load_legion_md(self) -> str:
        path = os.path.join(self.project_dir, "LEGION.md")
        if os.path.exists(path):
            with open(path) as f:
                return f.read()
        return ""

    def load_memory_files(self) -> str:
        parts = []
        md_path = os.path.join(self.project_dir, "LEGION.md")
        if os.path.exists(md_path):
            with open(md_path) as f:
                parts.append(f.read())
        extra_path = os.path.join(self.project_dir, ".legion", "memory.md")
        if os.path.exists(extra_path):
            with open(extra_path) as f:
                parts.append(f.read())
        return "\n\n".join(parts)


class AutoMemory:
    def __init__(self, store_path: str):
        self.store_path = store_path
        os.makedirs(os.path.dirname(store_path), exist_ok=True)

    def load_notes(self) -> list:
        if not os.path.exists(self.store_path):
            return []
        with open(self.store_path) as f:
            data = json.load(f)
        return data.get("notes", [])

    def add_note(self, note: str):
        notes = self.load_notes()
        notes.append({"text": note, "timestamp": time.time()})
        with open(self.store_path, "w") as f:
            json.dump({"notes": notes}, f, indent=2)

    def get_context(self) -> str:
        notes = self.load_notes()
        if not notes:
            return ""
        lines = ["Memory notes:"]
        for n in notes[-5:]:
            lines.append(f"- {n['text']}")
        return "\n".join(lines)


class MemoryManager:
    def __init__(self, session_dir: str, project_dir: str = None):
        self.session_store = SessionStore(session_dir)
        self.project_loader = ProjectContextLoader(project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        auto_memory_dir = os.path.join(session_dir, "auto_memory")
        self.auto_memory = AutoMemory(os.path.join(auto_memory_dir, "notes.json"))

    def save_session(self, session_id: str, config: dict, history: list, summary: str = "") -> str:
        data = {
            "config": config,
            "history": history,
            "summary": summary,
        }
        return self.session_store.save(session_id, data)

    def load_session(self, session_id: str) -> dict:
        return self.session_store.load(session_id)

    def list_sessions(self) -> list:
        return self.session_store.list_sessions()

    def get_latest_session(self) -> dict:
        return self.session_store.get_latest()

    def get_project_context(self) -> str:
        return self.project_loader.load_memory_files()

    def get_auto_memory_context(self) -> str:
        return self.auto_memory.get_context()

    def add_auto_note(self, note: str):
        self.auto_memory.add_note(note)

    def get_full_context(self) -> str:
        parts = []
        proj = self.get_project_context()
        if proj:
            parts.append(proj)
        auto = self.get_auto_memory_context()
        if auto:
            parts.append(auto)
        return "\n\n".join(parts)