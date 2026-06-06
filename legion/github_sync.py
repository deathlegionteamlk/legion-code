import os
import glob
from github import Github, GithubException


class GithubSync:
    def __init__(self, token: str = "", repo_name: str = ""):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo_name = repo_name
        self._g = Github(self.token) if self.token else None
        self._repo = None

    def set_token(self, token: str):
        self.token = token
        self._g = Github(token)

    def create_repo(self, name: str, private: bool = True, description: str = "") -> dict:
        if not self._g:
            raise ValueError("GitHub token not set")
        try:
            user = self._g.get_user()
            repo = user.create_repo(name, private=private, description=description or f"Legion Code - {name}")
            self._repo = repo
            self.repo_name = name
            return {"name": repo.full_name, "url": repo.html_url, "clone_url": repo.clone_url}
        except GithubException as e:
            if e.status == 422:
                repo = self._g.get_repo(f"{user.login}/{name}")
                self._repo = repo
                self.repo_name = name
                return {"name": repo.full_name, "url": repo.html_url, "clone_url": repo.clone_url, "exists": True}
            raise

    def push_code(self, file_patterns: list = None, branch: str = "main", commit_msg: str = "") -> dict:
        if not self._repo:
            raise ValueError("No repo. Call create_repo() first.")
        if file_patterns is None:
            file_patterns = ["*.py", "*.md", "*.txt", "*.json", "*.yaml", "*.yml", "*.cfg", "*.ini"]
        import base64
        results = {"pushed": [], "skipped": [], "errors": []}
        files_to_push = set()
        for pattern in file_patterns:
            for match in glob.glob(pattern, recursive=True):
                if os.path.isfile(match) and not match.startswith("."):
                    files_to_push.add(match)
        for fpath in sorted(files_to_push):
            try:
                with open(fpath, "rb") as f:
                    content = f.read()
                rel_path = os.path.relpath(fpath)
                try:
                    existing = self._repo.get_contents(rel_path, ref=branch)
                    if existing.sha:
                        self._repo.update_file(rel_path, commit_msg or f"Update {rel_path}", content, existing.sha, branch=branch)
                        results["pushed"].append(rel_path)
                except GithubException:
                    self._repo.create_file(rel_path, commit_msg or f"Add {rel_path}", content, branch=branch)
                    results["pushed"].append(rel_path)
            except Exception as e:
                results["errors"].append(f"{fpath}: {e}")
        return results

    def create_release(self, tag: str, title: str = "", notes: str = "") -> dict:
        if not self._repo:
            raise ValueError("No repo. Call create_repo() first.")
        try:
            release = self._repo.create_git_release(tag, title or tag, notes or f"Release {tag}")
            return {"tag": tag, "url": release.html_url, "id": release.id}
        except GithubException as e:
            return {"error": str(e)}

    def list_repos(self) -> list:
        if not self._g:
            raise ValueError("GitHub token not set")
        user = self._g.get_user()
        return [{"name": r.full_name, "url": r.html_url, "private": r.private} for r in user.get_repos()]