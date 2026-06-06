import sqlite3
import os
import json


def get_tool_definitions():
    return [
        {
            "name": "db_query",
            "description": "Execute a SQL query on a database (SQLite or PostgreSQL via config)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"},
                    "db_path": {"type": "string", "description": "Path to SQLite database file"},
                    "params": {"type": "array", "items": {"type": "string"}, "description": "Query parameters"},
                },
                "required": ["query"]
            },
            "handler": lambda args: _db_query(args.get("query", ""), args.get("db_path", ""), args.get("params", []))
        },
        {
            "name": "db_schema",
            "description": "Show database schema - tables, columns, types",
            "input_schema": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to SQLite database file"},
                },
                "required": ["db_path"]
            },
            "handler": lambda args: _db_schema(args.get("db_path", ""))
        },
        {
            "name": "db_backup",
            "description": "Backup a SQLite database",
            "input_schema": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to SQLite database file"},
                    "output_path": {"type": "string", "description": "Output backup path"},
                },
                "required": ["db_path"]
            },
            "handler": lambda args: _db_backup(args.get("db_path", ""), args.get("output_path", ""))
        },
        {
            "name": "db_migrate",
            "description": "Run database migrations from SQL file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "Path to SQLite database file"},
                    "migration_file": {"type": "string", "description": "Path to SQL migration file"},
                },
                "required": ["db_path", "migration_file"]
            },
            "handler": lambda args: _db_migrate(args.get("db_path", ""), args.get("migration_file", ""))
        },
    ]


def _db_query(query, db_path="", params=None):
    if not db_path:
        return "Error: db_path required"
    if not os.path.exists(db_path):
        return f"Error: database not found at {db_path}"
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        if query.strip().upper().startswith(("SELECT", "PRAGMA")):
            rows = [dict(r) for r in cur.fetchall()]
            conn.close()
            return json.dumps(rows, indent=2, default=str)
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return f"Query executed. {affected} rows affected."
    except Exception as e:
        return f"Database error: {e}"


def _db_schema(db_path=""):
    if not db_path or not os.path.exists(db_path):
        return f"Error: database not found at {db_path}"
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        schema = {}
        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [{"name": r[1], "type": r[2], "notnull": bool(r[3]), "default": r[4]} for r in cur.fetchall()]
            schema[table] = cols
        conn.close()
        return json.dumps(schema, indent=2)
    except Exception as e:
        return f"Schema error: {e}"


def _db_backup(db_path="", output_path=""):
    if not db_path or not os.path.exists(db_path):
        return f"Error: database not found at {db_path}"
    if not output_path:
        output_path = db_path + ".backup"
    try:
        conn = sqlite3.connect(db_path)
        bconn = sqlite3.connect(output_path)
        conn.backup(bconn)
        bconn.close()
        conn.close()
        return f"Backup created at {output_path}"
    except Exception as e:
        return f"Backup error: {e}"


def _db_migrate(db_path="", migration_file=""):
    if not db_path:
        return "Error: db_path required"
    if not migration_file or not os.path.exists(migration_file):
        return f"Error: migration file not found at {migration_file}"
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        with open(migration_file) as f:
            sql = f.read()
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                cur.execute(stmt)
        conn.commit()
        conn.close()
        return f"Migration {migration_file} applied successfully."
    except Exception as e:
        return f"Migration error: {e}"