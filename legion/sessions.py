import os
import json
import subprocess
import time
import signal
from datetime import datetime


class BackgroundSession:
    def __init__(self, session_id: str, command: str, workdir: str, log_path: str):
        self.session_id = session_id
        self.command = command
        self.workdir = workdir
        self.log_path = log_path
        self.process = None
        self.pid = None
        self.status = "created"
        self.started_at = None

    def start(self):
        log_dir = os.path.dirname(self.log_path)
        os.makedirs(log_dir, exist_ok=True)
        log_file = open(self.log_path, "w")
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            cwd=self.workdir,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,
        )
        self.pid = self.process.pid
        self.status = "running"
        self.started_at = datetime.now().isoformat()
        return self.pid

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception:
                    pass
        self.status = "stopped"

    def is_running(self) -> bool:
        if self.process is None:
            return False
        ret = self.process.poll()
        return ret is None

    def get_log(self, tail: int = 50) -> str:
        if not os.path.exists(self.log_path):
            return ""
        with open(self.log_path) as f:
            lines = f.readlines()
        return "".join(lines[-tail:])

    def to_dict(self) -> dict:
        return {
            "id": self.session_id,
            "pid": self.pid,
            "command": self.command,
            "status": self.status,
            "started_at": self.started_at,
            "log_path": self.log_path,
        }


class SessionManager:
    def __init__(self, sessions_dir: str):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
        self.background_sessions = {}
        self._load_persisted()

    def _load_persisted(self):
        state_path = os.path.join(self.sessions_dir, "_background_state.json")
        if os.path.exists(state_path):
            try:
                with open(state_path) as f:
                    data = json.load(f)
                for sid, info in data.items():
                    if info.get("status") == "running":
                        session = BackgroundSession(
                            session_id=sid,
                            command=info.get("command", ""),
                            workdir=info.get("workdir", os.getcwd()),
                            log_path=info.get("log_path", os.path.join(self.sessions_dir, f"{sid}.log")),
                        )
                        session.pid = info.get("pid")
                        session.status = "unknown"
                        session.started_at = info.get("started_at")
                        if not session.is_running():
                            session.status = "stopped"
                        self.background_sessions[sid] = session
            except Exception:
                pass

    def _persist_state(self):
        state_path = os.path.join(self.sessions_dir, "_background_state.json")
        data = {sid: s.to_dict() for sid, s in self.background_sessions.items()}
        try:
            with open(state_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def start_background(self, command: str, workdir: str = None) -> str:
        session_id = f"bg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        log_path = os.path.join(self.sessions_dir, f"{session_id}.log")
        session = BackgroundSession(session_id, command, workdir or os.getcwd(), log_path)
        session.start()
        self.background_sessions[session_id] = session
        self._persist_state()
        return session_id

    def list_sessions(self) -> list:
        self._cleanup_stale()
        return [s.to_dict() for s in self.background_sessions.values()]

    def get_session(self, session_id: str) -> BackgroundSession:
        return self.background_sessions.get(session_id)

    def stop_session(self, session_id: str) -> bool:
        session = self.background_sessions.get(session_id)
        if session:
            session.stop()
            self._persist_state()
            return True
        return False

    def _cleanup_stale(self):
        to_remove = []
        for sid, session in self.background_sessions.items():
            if session.status == "running" and not session.is_running():
                session.status = "stopped"
                to_remove.append(sid)
        for sid in to_remove:
            del self.background_sessions[sid]
        if to_remove:
            self._persist_state()