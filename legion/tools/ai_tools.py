import json


def get_tool_definitions():
    return [
        {
            "name": "embed_text",
            "description": "Generate embeddings for text using configured AI provider",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to embed"},
                    "model": {"type": "string", "description": "Embedding model name"},
                },
                "required": ["text"]
            },
            "handler": lambda args: _embed_text(args.get("text", ""), args.get("model", ""))
        },
        {
            "name": "classify_text",
            "description": "Classify text into predefined categories using AI",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to classify"},
                    "categories": {"type": "string", "description": "Comma-separated list of categories"},
                },
                "required": ["text"]
            },
            "handler": lambda args: _classify_text(args.get("text", ""), args.get("categories", ""))
        },
        {
            "name": "extract_entities",
            "description": "Extract named entities from text",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to extract entities from"},
                },
                "required": ["text"]
            },
            "handler": lambda args: _extract_entities(args.get("text", ""))
        },
        {
            "name": "summarization",
            "description": "Summarize text content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_length": {"type": "integer", "description": "Maximum summary length in words"},
                },
                "required": ["text"]
            },
            "handler": lambda args: _summarization(args.get("text", ""), args.get("max_length", 100))
        },
        {
            "name": "translate_text",
            "description": "Translate text between languages",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "target_language": {"type": "string", "description": "Target language (e.g., spanish, french)"},
                },
                "required": ["text", "target_language"]
            },
            "handler": lambda args: _translate_text(args.get("text", ""), args.get("target_language", ""))
        },
        {
            "name": "generate_image",
            "description": "Generate an image from a text description (stub - requires API key)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description prompt"},
                    "size": {"type": "string", "description": "Image size (e.g., 1024x1024)"},
                },
                "required": ["prompt"]
            },
            "handler": lambda args: _generate_image(args.get("prompt", ""), args.get("size", "1024x1024"))
        },
    ]


def _embed_text(text="", model=""):
    if not text:
        return "Error: text required"
    return json.dumps({
        "tool": "embed_text",
        "text_length": len(text),
        "model": model or "default",
        "status": "stub",
        "note": "Embeddings require configured AI provider with embedding support",
    }, indent=2)


def _classify_text(text="", categories=""):
    if not text:
        return "Error: text required"
    cats = [c.strip() for c in categories.split(",")] if categories else ["positive", "negative", "neutral"]
    return json.dumps({
        "tool": "classify_text",
        "text_length": len(text),
        "categories": cats,
        "status": "stub",
        "note": "Classification requires configured AI provider",
    }, indent=2)


def _extract_entities(text=""):
    if not text:
        return "Error: text required"
    return json.dumps({
        "tool": "extract_entities",
        "text_length": len(text),
        "status": "stub",
        "note": "Entity extraction requires configured AI provider",
    }, indent=2)


def _summarization(text="", max_length=100):
    if not text:
        return "Error: text required"
    return json.dumps({
        "tool": "summarization",
        "text_length": len(text),
        "max_length": max_length,
        "status": "stub",
        "note": "Summarization requires configured AI provider",
    }, indent=2)


def _translate_text(text="", target_language=""):
    if not text:
        return "Error: text required"
    if not target_language:
        return "Error: target_language required"
    return json.dumps({
        "tool": "translate_text",
        "text_length": len(text),
        "target_language": target_language,
        "status": "stub",
        "note": "Translation requires configured AI provider",
    }, indent=2)


def _generate_image(prompt="", size="1024x1024"):
    if not prompt:
        return "Error: prompt required"
    return json.dumps({
        "tool": "generate_image",
        "prompt": prompt[:100],
        "size": size,
        "status": "stub",
        "note": "Image generation requires configured AI provider with image API key",
    }, indent=2)