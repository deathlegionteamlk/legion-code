import urllib.request
import urllib.parse
import re
from legion.config import Config
from legion.provider import Provider

RESEARCHER_PROMPT = """You are a research analyst. Given search results on a topic, synthesize the findings into a structured report.

Format your report with:
1. Summary: 2-3 sentence overview
2. Key Findings: bullet points of the most important discoveries
3. Analysis: your assessment of the information
4. Sources: the URLs referenced

Focus on extracting concrete, actionable information."""

class Researcher:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.provider = Provider(self.config)

    def search(self, query: str, max_results: int = 5) -> str:
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
            return "\n".join(output_lines)
        except Exception as e:
            return f"Search error: {e}"

    def synthesize(self, topic: str, search_results: str) -> str:
        messages = [
            {"role": "user", "content": f"Research topic: {topic}\n\nSearch results:\n{search_results}\n\nSynthesize these findings into a structured report."}
        ]
        try:
            response = self.provider.chat(messages, system_prompt=RESEARCHER_PROMPT)
            message = self.provider.extract_assistant_message(response)
            return message.get("content", "No report generated")
        except Exception as e:
            return f"Research synthesis failed: {e}"

    def research(self, topic: str) -> str:
        results = self.search(topic)
        if results.startswith("Search error"):
            return results
        report = self.synthesize(topic, results)
        return f"Research Report: {topic}\n{'='*60}\n{report}"

    def close(self):
        self.provider.close()