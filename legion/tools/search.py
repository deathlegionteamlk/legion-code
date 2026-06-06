import urllib.request
import urllib.parse
import json
import re

def internet_search(query: str, max_results: int = 5) -> str:
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; LegionCode/1.0)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        results = []
        for match in re.finditer(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL):
            href = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if href and title:
                results.append({"title": title, "url": href})
        for match in re.finditer(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL):
            snippet_text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if len(results) > len([r for r in results]):
                pass
        snippet_matches = list(re.finditer(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL))
        for i, sm in enumerate(snippet_matches):
            if i < len(results):
                results[i]["snippet"] = re.sub(r'<[^>]+>', '', sm.group(1)).strip()
        limited = results[:max_results]
        if not limited:
            for match in re.finditer(r'<h2[^>]*>(.*?)</h2>', html, re.DOTALL):
                title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if title:
                    limited.append({"title": title, "url": "", "snippet": ""})
            limited = limited[:max_results]
        output_lines = [f"Search results for: {query}"]
        for i, r in enumerate(limited, 1):
            output_lines.append(f"\n{i}. {r.get('title', 'Untitled')}")
            if r.get("url"):
                output_lines.append(f"   URL: {r['url']}")
            if r.get("snippet"):
                output_lines.append(f"   {r['snippet']}")
        return "\n".join(output_lines) if output_lines else "No results found"
    except Exception as e:
        return f"Search error: {e}"

def get_tool_definitions():
    return [
        {
            "name": "internet_search",
            "description": "Search the internet for information using DuckDuckGo. Returns ranked results with titles, URLs, and snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query with 3-5 keywords"},
                    "max_results": {"type": "integer", "description": "Maximum results to return", "default": 5}
                },
                "required": ["query"]
            },
            "handler": lambda args: internet_search(args.get("query", ""), args.get("max_results", 5))
        },
    ]