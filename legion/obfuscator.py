import os
import subprocess
import shutil


class Obfuscator:
    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir

    def protect_file(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        try:
            result = subprocess.run(
                ["pyarmor", "obfuscate", "-O", self.output_dir, filepath],
                capture_output=True, text=True, timeout=60
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"pyarmor timed out on {filepath}")
        except FileNotFoundError:
            raise RuntimeError("pyarmor not installed. Run: pip install pyarmor")

    def protect_all(self, path: str) -> list:
        protected = []
        py_files = []
        for root, dirs, files in os.walk(path):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))
        for fpath in py_files:
            try:
                if self.protect_file(fpath):
                    protected.append(fpath)
            except Exception:
                pass
        return protected

    def build_dist(self, source_dirs: list = None) -> str:
        if source_dirs is None:
            source_dirs = ["legion"]
        dist_path = os.path.abspath(self.output_dir)
        os.makedirs(dist_path, exist_ok=True)
        all_files = []
        for sd in source_dirs:
            if os.path.isdir(sd):
                all_files.extend(self.protect_all(sd))
        return dist_path