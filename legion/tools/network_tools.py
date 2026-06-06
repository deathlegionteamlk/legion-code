import socket
import json
import urllib.request
import urllib.error
import subprocess
import platform


def get_tool_definitions():
    return [
        {
            "name": "http_request",
            "description": "Make HTTP requests (GET, POST, PUT, DELETE) and return response",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "data": {"type": "string", "description": "Request body data (JSON string)"},
                    "headers": {"type": "string", "description": "JSON string of headers"},
                },
                "required": ["url"]
            },
            "handler": lambda args: _http_request(args.get("url", ""), args.get("method", "GET"), args.get("data"), args.get("headers"))
        },
        {
            "name": "ping_test",
            "description": "Test network connectivity to a host",
            "input_schema": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Hostname or IP to ping"},
                    "count": {"type": "integer", "description": "Number of ping packets"},
                },
                "required": ["host"]
            },
            "handler": lambda args: _ping_test(args.get("host", ""), args.get("count", 3))
        },
        {
            "name": "dns_lookup",
            "description": "Perform DNS lookup for a hostname",
            "input_schema": {
                "type": "object",
                "properties": {
                    "hostname": {"type": "string", "description": "Hostname to resolve"},
                },
                "required": ["hostname"]
            },
            "handler": lambda args: _dns_lookup(args.get("hostname", ""))
        },
        {
            "name": "port_scan",
            "description": "Scan TCP ports on a host",
            "input_schema": {
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "Hostname or IP"},
                    "ports": {"type": "string", "description": "Comma-separated ports or range like '80,443,8000-8100'"},
                    "timeout": {"type": "integer", "description": "Connection timeout in seconds"},
                },
                "required": ["host"]
            },
            "handler": lambda args: _port_scan(args.get("host", ""), args.get("ports", "80,443"), args.get("timeout", 2))
        },
        {
            "name": "api_discover",
            "description": "Discover API endpoints from OpenAPI/Swagger spec URL",
            "input_schema": {
                "type": "object",
                "properties": {
                    "spec_url": {"type": "string", "description": "URL to OpenAPI/Swagger JSON spec"},
                },
                "required": ["spec_url"]
            },
            "handler": lambda args: _api_discover(args.get("spec_url", ""))
        },
    ]


def _http_request(url="", method="GET", data=None, headers=None):
    if not url:
        return "Error: URL required"
    try:
        if isinstance(headers, str):
            headers = json.loads(headers) if headers else {}
        elif headers is None:
            headers = {}
        req = urllib.request.Request(url, method=method, headers=headers)
        if data:
            if isinstance(data, str):
                req.data = data.encode("utf-8")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.dumps({"status": resp.status, "headers": dict(resp.headers), "body": body[:5000]}, indent=2)
    except urllib.error.HTTPError as e:
        return json.dumps({"status": e.code, "error": str(e)}, indent=2)
    except Exception as e:
        return f"HTTP request error: {e}"


def _ping_test(host="", count=3):
    if not host:
        return "Error: host required"
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(["ping", param, str(count), host], capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return f"Ping results for {host}:\n{output[:2000]}"
    except subprocess.TimeoutExpired:
        return f"Ping timed out for {host}"
    except FileNotFoundError:
        return "Ping command not available in this environment"
    except Exception as e:
        return f"Ping error: {e}"


def _dns_lookup(hostname=""):
    if not hostname:
        return "Error: hostname required"
    try:
        addrs = socket.getaddrinfo(hostname, None)
        results = set()
        for addr in addrs:
            results.add(addr[4][0])
        return f"DNS records for {hostname}:\n" + "\n".join(f"  {r}" for r in sorted(results))
    except socket.gaierror as e:
        return f"DNS lookup failed for {hostname}: {e}"
    except Exception as e:
        return f"DNS error: {e}"


def _port_scan(host="", ports="80,443", timeout=2):
    if not host:
        return "Error: host required"
    try:
        port_list = []
        for part in ports.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-", 1)
                port_list.extend(range(int(start), int(end) + 1))
            else:
                port_list.append(int(part))
        open_ports = []
        for port in port_list[:100]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        if open_ports:
            return f"Open ports on {host}: {', '.join(str(p) for p in open_ports)}"
        return f"No open ports found on {host} in range {ports}"
    except Exception as e:
        return f"Port scan error: {e}"


def _api_discover(spec_url=""):
    if not spec_url:
        return "Error: spec_url required"
    try:
        req = urllib.request.Request(spec_url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            spec = json.loads(resp.read().decode("utf-8"))
        endpoints = []
        if "paths" in spec:
            for path, methods in spec["paths"].items():
                for method in methods:
                    if method.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        info = methods[method]
                        endpoints.append({
                            "path": path,
                            "method": method.upper(),
                            "summary": info.get("summary", ""),
                            "operationId": info.get("operationId", ""),
                        })
        summary = {"title": spec.get("info", {}).get("title", ""), "version": spec.get("info", {}).get("version", ""), "endpoints": endpoints}
        return json.dumps(summary, indent=2)
    except Exception as e:
        return f"API discovery error: {e}"