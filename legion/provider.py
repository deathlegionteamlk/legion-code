import json
import time
import random
import httpx
from typing import Optional, Generator, Any
from legion.config import Config


class ProviderError(Exception):
    pass


class Provider:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.chat_url = f"{self.config.api_base}/chat/completions"
        self._client: Optional[httpx.Client] = None
        self._retry_count = 3
        self._retry_delay = 1.0

    @property
    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/legion-code",
            "X-Title": "Legion Code",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(headers=self._headers, timeout=self.config.request_timeout)
        return self._client

    def _format_messages(self, messages: list[dict], system_prompt: Optional[str] = None, tools: Optional[list[dict]] = None) -> list[dict]:
        formatted = list(messages)
        if system_prompt:
            has_system = any(m.get("role") == "system" for m in formatted)
            if has_system:
                for i, m in enumerate(formatted):
                    if m["role"] == "system":
                        formatted[i] = {"role": "system", "content": system_prompt}
                        break
            else:
                formatted.insert(0, {"role": "system", "content": system_prompt})
        return formatted

    def _build_payload(self, messages: list[dict], tools: Optional[list[dict]] = None, stream: bool = False) -> dict:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "stream": stream,
        }
        if tools:
            payload["tools"] = tools
        return payload

    def _extract_token_usage(self, response: dict) -> dict:
        usage = response.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cache_read": usage.get("prompt_tokens_details", {}).get("cached_tokens", 0) if isinstance(usage.get("prompt_tokens_details"), dict) else 0,
        }

    def _report_usage(self, usage: dict):
        try:
            from legion.cost_tracker import CostTracker
            tracker = CostTracker()
            tracker.record_usage(
                model=self.config.model,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                cache_read=usage.get("cache_read", 0),
            )
        except Exception:
            pass

    def chat(self, messages: list[dict], system_prompt: Optional[str] = None, tools: Optional[list[dict]] = None) -> dict:
        formatted = self._format_messages(messages, system_prompt)
        payload = self._build_payload(formatted, tools, stream=False)
        last_error = None
        for attempt in range(self._retry_count):
            try:
                client = self._get_client()
                response = client.post(self.chat_url, json=payload)
                response.raise_for_status()
                data = response.json()
                usage = self._extract_token_usage(data)
                self._report_usage(usage)
                return data
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                error_detail = ""
                try:
                    error_detail = e.response.text
                except Exception:
                    error_detail = str(e)
                if status == 401:
                    raise ProviderError("Authentication failed (401): check OPENROUTER_API_KEY")
                elif status == 403:
                    raise ProviderError("Forbidden (403): model may be restricted or credits exhausted")
                elif status == 429:
                    delay = (2 ** attempt) * self._retry_delay + random.uniform(0, 1)
                    time.sleep(delay)
                    last_error = ProviderError(f"Rate limited (429), retry {attempt + 1}/{self._retry_count}")
                    continue
                elif status >= 500:
                    delay = (2 ** attempt) * self._retry_delay
                    time.sleep(delay)
                    last_error = ProviderError(f"Server error ({status}), retry {attempt + 1}/{self._retry_count}")
                    continue
                raise ProviderError(f"HTTP {status}: {error_detail}")
            except httpx.TimeoutException:
                delay = (2 ** attempt) * self._retry_delay
                time.sleep(delay)
                last_error = ProviderError(f"Request timed out after {self.config.request_timeout}s, retry {attempt + 1}/{self._retry_count}")
            except httpx.RequestError as e:
                delay = (2 ** attempt) * self._retry_delay
                time.sleep(delay)
                last_error = ProviderError(f"Request failed: {e}, retry {attempt + 1}/{self._retry_count}")
        raise last_error or ProviderError("Request failed after all retries")

    def chat_stream(self, messages: list[dict], system_prompt: Optional[str] = None, tools: Optional[list[dict]] = None) -> Generator[dict, None, None]:
        formatted = self._format_messages(messages, system_prompt)
        payload = self._build_payload(formatted, tools, stream=True)
        client = self._get_client()
        try:
            with client.stream("POST", self.chat_url, json=payload) as response:
                response.raise_for_status()
                current_tool_calls = {}
                for line in response.iter_lines():
                    if not line or line.startswith(":"):
                        continue
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        choices = data.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield {"type": "text", "content": content}
                        if "tool_calls" in delta:
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in current_tool_calls:
                                    current_tool_calls[idx] = {"id": "", "function": {"name": "", "arguments": ""}}
                                if tc.get("id"):
                                    current_tool_calls[idx]["id"] = tc["id"]
                                func = tc.get("function", {})
                                if func.get("name"):
                                    current_tool_calls[idx]["function"]["name"] = func["name"]
                                if func.get("arguments"):
                                    current_tool_calls[idx]["function"]["arguments"] += func["arguments"]
                        finish_reason = choices[0].get("finish_reason")
                        if finish_reason == "tool_calls" and current_tool_calls:
                            for idx, tc_data in current_tool_calls.items():
                                args_str = tc_data["function"]["arguments"]
                                try:
                                    args = json.loads(args_str) if args_str else {}
                                except json.JSONDecodeError:
                                    args = {}
                                yield {
                                    "type": "tool_call",
                                    "tool_call_id": tc_data["id"],
                                    "name": tc_data["function"]["name"],
                                    "arguments": args,
                                }
                            current_tool_calls.clear()
                        if finish_reason == "stop":
                            break
        except httpx.HTTPStatusError as e:
            error_text = ""
            try:
                error_text = e.response.text
            except Exception:
                error_text = str(e)
            raise ProviderError(f"HTTP {e.response.status_code}: {error_text}")
        except httpx.TimeoutException:
            raise ProviderError("Stream request timed out")
        except httpx.RequestError as e:
            raise ProviderError(f"Stream request failed: {e}")

    def extract_assistant_message(self, response: dict) -> dict:
        choices = response.get("choices", [])
        if not choices:
            raise ProviderError("No choices in response")
        return choices[0].get("message", {})

    def extract_tool_calls(self, message: dict) -> list[dict]:
        raw_calls = message.get("tool_calls", [])
        calls = []
        for tc in raw_calls:
            if tc.get("type") == "function":
                func = tc.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                calls.append({
                    "id": tc.get("id", ""),
                    "type": "function",
                    "function": {"name": func.get("name", ""), "arguments": args},
                })
        return calls

    def format_tool_result(self, tool_call: dict, result: Any) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call.get("id", ""),
            "content": json.dumps(result) if not isinstance(result, str) else str(result),
        }

    def switch_model(self, model: str):
        self.config.model = model

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()