import os
import hashlib
import difflib
import zipfile
import tarfile
import shutil
import json
import time
from datetime import datetime


def get_tool_definitions():
    return [
        {
            "name": "file_diff",
            "description": "Show diff between two files",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file1": {"type": "string", "description": "Path to first file"},
                    "file2": {"type": "string", "description": "Path to second file"},
                    "context_lines": {"type": "integer", "description": "Number of context lines"},
                },
                "required": ["file1", "file2"]
            },
            "handler": lambda args: _file_diff(args.get("file1", ""), args.get("file2", ""), args.get("context_lines", 3))
        },
        {
            "name": "file_merge",
            "description": "Merge two files with conflict markers",
            "input_schema": {
                "type": "object",
                "properties": {
                    "base_file": {"type": "string", "description": "Base file path"},
                    "modified_file": {"type": "string", "description": "Modified file path"},
                    "output_file": {"type": "string", "description": "Output merged file path"},
                },
                "required": ["base_file", "modified_file"]
            },
            "handler": lambda args: _file_merge(args.get("base_file", ""), args.get("modified_file", ""), args.get("output_file", ""))
        },
        {
            "name": "batch_rename",
            "description": "Rename files matching a pattern",
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory containing files"},
                    "pattern": {"type": "string", "description": "Glob pattern to match files"},
                    "find_text": {"type": "string", "description": "Text to find in filename"},
                    "replace_text": {"type": "string", "description": "Text to replace with"},
                },
                "required": ["directory"]
            },
            "handler": lambda args: _batch_rename(args.get("directory", ""), args.get("pattern", "*"), args.get("find_text", ""), args.get("replace_text", ""))
        },
        {
            "name": "file_stat",
            "description": "Get detailed file statistics",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file or directory"},
                },
                "required": ["path"]
            },
            "handler": lambda args: _file_stat(args.get("path", ""))
        },
        {
            "name": "file_find_duplicates",
            "description": "Find duplicate files by hash",
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to scan"},
                    "pattern": {"type": "string", "description": "Glob pattern to match files"},
                },
                "required": ["directory"]
            },
            "handler": lambda args: _file_find_duplicates(args.get("directory", ""), args.get("pattern", "*"))
        },
        {
            "name": "archive_extract",
            "description": "Extract zip or tar archive",
            "input_schema": {
                "type": "object",
                "properties": {
                    "archive_path": {"type": "string", "description": "Path to archive file"},
                    "extract_dir": {"type": "string", "description": "Directory to extract into"},
                },
                "required": ["archive_path"]
            },
            "handler": lambda args: _archive_extract(args.get("archive_path", ""), args.get("extract_dir", ""))
        },
        {
            "name": "archive_create",
            "description": "Create zip or tar archive",
            "input_schema": {
                "type": "object",
                "properties": {
                    "output_path": {"type": "string", "description": "Output archive path"},
                    "source_dir": {"type": "string", "description": "Source directory to archive"},
                    "archive_type": {"type": "string", "description": "Archive type: zip or tar.gz"},
                },
                "required": ["output_path", "source_dir"]
            },
            "handler": lambda args: _archive_create(args.get("output_path", ""), args.get("source_dir", ""), args.get("archive_type", "zip"))
        },
        {
            "name": "file_watch",
            "description": "Watch a directory for file changes (one-time snapshot)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to watch"},
                },
                "required": ["directory"]
            },
            "handler": lambda args: _file_watch(args.get("directory", ""))
        },
    ]


def _file_diff(file1="", file2="", context_lines=3):
    if not os.path.exists(file1):
        return f"Error: file not found: {file1}"
    if not os.path.exists(file2):
        return f"Error: file not found: {file2}"
    try:
        with open(file1) as f:
            lines1 = f.readlines()
        with open(file2) as f:
            lines2 = f.readlines()
        diff = difflib.unified_diff(lines1, lines2, fromfile=file1, tofile=file2, n=context_lines)
        result = "".join(diff)
        return result if result else "Files are identical"
    except Exception as e:
        return f"Diff error: {e}"


def _file_merge(base_file="", modified_file="", output_file=""):
    if not os.path.exists(base_file):
        return f"Error: base file not found: {base_file}"
    if not os.path.exists(modified_file):
        return f"Error: modified file not found: {modified_file}"
    if not output_file:
        output_file = base_file + ".merged"
    try:
        with open(base_file) as f:
            base_lines = f.readlines()
        with open(modified_file) as f:
            mod_lines = f.readlines()
        diff = list(difflib.unified_diff(base_lines, mod_lines, n=0))
        merged = []
        base_idx = 0
        mod_idx = 0
        i = 0
        while i < len(diff):
            line = diff[i]
            if line.startswith("@@"):
                parts = line.split()
                base_range = parts[1]
                mod_range = parts[2]
                b_start = int(base_range.split(",")[0].lstrip("-")) - 1 if "," in base_range else int(base_range) - 1
                b_count = int(base_range.split(",")[1]) if "," in base_range else 1
                m_start = int(mod_range.split(",")[0].lstrip("+")) - 1 if "," in mod_range else int(mod_range) - 1
                m_count = int(mod_range.split(",")[1]) if "," in mod_range else 1
                while base_idx < b_start:
                    merged.append(base_lines[base_idx])
                    base_idx += 1
                i += 1
                while i < len(diff) and not diff[i].startswith("@@"):
                    dline = diff[i]
                    if dline.startswith("-"):
                        base_idx += 1
                    elif dline.startswith("+"):
                        merged.append(dline[1:])
                        mod_idx += 1
                    else:
                        merged.append(dline[1:])
                        base_idx += 1
                        mod_idx += 1
                    i += 1
            else:
                i += 1
        while base_idx < len(base_lines):
            merged.append(base_lines[base_idx])
            base_idx += 1
        with open(output_file, "w") as f:
            f.writelines(merged)
        return f"Merged file written to {output_file}"
    except Exception as e:
        return f"Merge error: {e}"


def _batch_rename(directory="", pattern="*", find_text="", replace_text=""):
    if not os.path.isdir(directory):
        return f"Error: directory not found: {directory}"
    try:
        import glob
        renamed = []
        for fpath in glob.glob(os.path.join(directory, pattern)):
            fname = os.path.basename(fpath)
            if find_text and find_text in fname:
                new_name = fname.replace(find_text, replace_text)
                new_path = os.path.join(directory, new_name)
                os.rename(fpath, new_path)
                renamed.append(f"{fname} -> {new_name}")
        if renamed:
            return "Renamed files:\n" + "\n".join(renamed)
        return "No files matched the rename criteria."
    except Exception as e:
        return f"Batch rename error: {e}"


def _file_stat(path=""):
    if not os.path.exists(path):
        return f"Error: path not found: {path}"
    try:
        if os.path.isfile(path):
            stat = os.stat(path)
            return json.dumps({
                "type": "file",
                "size": stat.st_size,
                "size_formatted": _format_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
            }, indent=2)
        elif os.path.isdir(path):
            total_size = 0
            file_count = 0
            dir_count = 0
            for root, dirs, files in os.walk(path):
                if "__pycache__" in root:
                    continue
                dir_count += len(dirs)
                file_count += len(files)
                for f in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            return json.dumps({
                "type": "directory",
                "total_size": total_size,
                "size_formatted": _format_size(total_size),
                "files": file_count,
                "directories": dir_count,
                "modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
            }, indent=2)
        return "Unknown path type"
    except Exception as e:
        return f"File stat error: {e}"


def _format_size(size):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def _file_find_duplicates(directory="", pattern="*"):
    if not os.path.isdir(directory):
        return f"Error: directory not found: {directory}"
    try:
        import glob
        hashes = {}
        for fpath in glob.glob(os.path.join(directory, pattern), recursive=True):
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                h = hashlib.md5(content).hexdigest()
                if h not in hashes:
                    hashes[h] = []
                hashes[h].append(fpath)
        duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
        if not duplicates:
            return "No duplicate files found."
        result_parts = [f"Found {len(duplicates)} sets of duplicate files:"]
        for h, paths in duplicates.items():
            result_parts.append(f"\nMD5: {h}")
            for p in paths:
                result_parts.append(f"  - {p}")
        return "\n".join(result_parts)
    except Exception as e:
        return f"Duplicate find error: {e}"


def _archive_extract(archive_path="", extract_dir=""):
    if not os.path.exists(archive_path):
        return f"Error: archive not found: {archive_path}"
    if not extract_dir:
        extract_dir = os.path.splitext(os.path.basename(archive_path))[0]
    os.makedirs(extract_dir, exist_ok=True)
    try:
        if archive_path.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(extract_dir)
        elif archive_path.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(extract_dir)
        elif archive_path.endswith(".tar"):
            with tarfile.open(archive_path, "r:") as tf:
                tf.extractall(extract_dir)
        elif archive_path.endswith(".tar.bz2"):
            with tarfile.open(archive_path, "r:bz2") as tf:
                tf.extractall(extract_dir)
        else:
            return f"Unsupported archive format: {archive_path}"
        items = os.listdir(extract_dir)
        return f"Extracted {len(items)} items to {extract_dir}"
    except Exception as e:
        return f"Extraction error: {e}"


def _archive_create(output_path="", source_dir="", archive_type="zip"):
    if not os.path.isdir(source_dir):
        return f"Error: source directory not found: {source_dir}"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    try:
        if archive_type == "zip":
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(source_dir):
                    for f in files:
                        fpath = os.path.join(root, f)
                        arcname = os.path.relpath(fpath, os.path.dirname(source_dir))
                        zf.write(fpath, arcname)
        elif archive_type in ("tar.gz", "tar"):
            mode = "w:gz" if archive_type == "tar.gz" else "w"
            with tarfile.open(output_path, mode) as tf:
                tf.add(source_dir, arcname=os.path.basename(source_dir))
        else:
            return f"Unsupported archive type: {archive_type}"
        return f"Archive created: {output_path} ({_format_size(os.path.getsize(output_path))})"
    except Exception as e:
        return f"Archive creation error: {e}"


def _file_watch(directory=""):
    if not os.path.isdir(directory):
        return f"Error: directory not found: {directory}"
    try:
        snapshot = {}
        for root, dirs, files in os.walk(directory):
            if "__pycache__" in root or ".git" in root:
                continue
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    stat = os.stat(fpath)
                    snapshot[fpath] = {"size": stat.st_size, "mtime": stat.st_mtime}
                except Exception:
                    pass
        return json.dumps({
            "directory": directory,
            "files_tracked": len(snapshot),
            "snapshot_time": datetime.now().isoformat(),
            "files": list(snapshot.keys()),
        }, indent=2)
    except Exception as e:
        return f"Watch error: {e}"