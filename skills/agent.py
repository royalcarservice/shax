from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from skills.file_manager import create_file, create_folder, list_files, read_file, edit_file as fm_edit_file
from skills.website_builder import create_website as website_builder_create_website

MODEL = "qwen2.5-coder:7b"
DB_NAME = Path(__file__).resolve().parent.parent / "memory.db"


def _ollama_chat(*args, **kwargs):
    """Lazy-load Ollama so local parser/tests do not require the package."""
    from ollama import chat
    return chat(*args, **kwargs)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

def _ensure_memory_table() -> None:
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, memory TEXT NOT NULL)"
        )


def get_memories() -> list[str]:
    try:
        _ensure_memory_table()
        with sqlite3.connect(DB_NAME) as connection:
            rows = connection.execute("SELECT memory FROM memories ORDER BY id").fetchall()
        return [row[0] for row in rows]
    except Exception:
        return []


def get_memory() -> str:
    memories = get_memories()
    if not memories:
        return "No long-term memories are currently saved."
    return "\n".join(f"{i}. {value}" for i, value in enumerate(memories, 1))


def save_memory(memory: str | None = None, key: str | None = None, value: str | None = None) -> str:
    if memory is None:
        if key is not None and value is not None:
            memory = f"{key}: {value}"
        else:
            memory = key or value
    memory = str(memory or "").strip()
    if not memory:
        return "Memory was empty; nothing was saved."
    _ensure_memory_table()
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("INSERT INTO memories (memory) VALUES (?)", (memory,))
    return f"Memory saved: {memory}"


def forget_memory(memory: str | None = None, key: str | None = None, value: str | None = None) -> str:
    needle = str(memory or key or value or "").strip()
    if not needle:
        return "Please provide the memory text to forget."
    _ensure_memory_table()
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.execute("DELETE FROM memories WHERE memory LIKE ?", (f"%{needle}%",))
        deleted = cursor.rowcount
    return f"Forgot {deleted} matching memory/memories." if deleted else "No matching memory was found."


def get_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Website routing
# ---------------------------------------------------------------------------

_WEBSITE_START = (
    "build a website", "make a website", "create a website", "design a website",
    "build me a website", "make me a website", "create me a website",
    "i want a website", "i need a website", "website for my business",
    "website for my company", "website for my brand", "build a site", "make a site",
    "create a site",
)

_WEBSITE_CONFIRMATIONS = {
    "yes", "yes build it", "build it", "build it now", "create it", "create it now",
    "make it", "go ahead", "do it", "start building", "start building it",
    "generate it", "generate the website", "create the website", "build the website",
    "make the website", "yes please", "that's all", "that is all", "looks good",
    "everything is good",
}


def _is_website_start(text: str) -> bool:
    """Detect website intent even when users insert adjectives/details.

    Examples that must all route to the website builder:
    - build a website for a coffee shop
    - build a modern website for a coffee shop
    - create a premium responsive site for my gym
    - design a simple portfolio website
    """
    lower = re.sub(r"\s+", " ", str(text or "").lower().strip())
    if any(phrase in lower for phrase in _WEBSITE_START):
        return True
    return bool(re.search(
        r"\b(?:build|create|make|design|develop|generate)\b(?:\s+(?:me|us|a|an|the|my|our|your|modern|premium|professional|simple|responsive|beautiful|clean|cool|new|custom|full|complete|landing|business|personal|modern|high[- ]end))*\s+(?:a\s+)?(?:website|site|webpage)\b",
        lower,
    ))


def _is_explicit_build(text: str) -> bool:
    lower = re.sub(r"\s+", " ", str(text or "").lower().strip())
    if any(phrase in lower for phrase in (
        "build it now", "create it now", "generate it now", "make it now",
        "go ahead and build", "go ahead and create", "start building",
    )):
        return True
    return bool(re.search(
        r"\b(?:build|create|make|design|develop|generate)\b.*\b(?:website|site|webpage)\b",
        lower,
    ))


def _previous_assistant_requested_build(history: list[dict[str, Any]]) -> bool:
    for message in reversed(history):
        if message.get("role") != "assistant":
            continue
        text = str(message.get("content", "")).lower()
        return any(phrase in text for phrase in (
            "shall i build", "should i build", "want me to build", "ready to build",
            "i have everything i need", "i have enough information", "shall i create",
        ))
    return False


def _collect_current_website_context(history: list[dict[str, Any]], current: str) -> str:
    """Return only user messages belonging to the latest website project.

    The last explicit website-start message is the project boundary. Assistant
    messages and older website projects are intentionally excluded.
    """
    user_messages = [
        str(message.get("content", "")).strip()
        for message in history
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    user_messages.append(str(current).strip())

    boundary = 0
    for index, message in enumerate(user_messages):
        if _is_website_start(message):
            boundary = index
    selected = user_messages[boundary:]
    return "\n\n".join(selected)


def _website_has_enough_context(context: str) -> bool:
    lower = context.lower()
    business = any(x in lower for x in (
        "for a ", "for an ", "for the ", "called ", "named ", "business is", "company is",
        "brand is", "i run", "i own", "we are a", "we are an",
    ))
    type_info = any(x in lower for x in (
        "coffee", "cafe", "garage", "mechanic", "automotive", "restaurant", "salon",
        "gym", "fitness", "shop", "store", "boutique", "agency", "consulting", "law firm",
        "services", "products", "portfolio",
    ))
    return business and type_info


def _website_planning_reply(context: str) -> str:
    try:
        prompt = f"""You are Shaqs helping plan a website.

CURRENT WEBSITE REQUEST:
{context}

Ask only ONE concise question for the most important missing detail.
Never ask for facts that are already present. Never invent business facts.
If the request already contains enough information to build a useful site, reply exactly:
I have everything I need. Shall I build it?
"""
        response = _ollama_chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        answer = str(getattr(response.message, "content", "") or "").strip()
        return answer or "What is the business or project name?"
    except Exception:
        return "What is the business or project name?"


def _handle_website_request(user_message: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]] | None:
    lower = user_message.lower().strip()
    started = _is_website_start(user_message)
    confirmed = lower in _WEBSITE_CONFIRMATIONS and _previous_assistant_requested_build(history)
    if not started and not confirmed:
        return None

    context = _collect_current_website_context(history, user_message)
    if confirmed:
        # Do not include the confirmation itself in the builder's factual input.
        context = _collect_current_website_context(history, "")

    should_build = _is_explicit_build(user_message) or confirmed
    if started and not should_build:
        should_build = _website_has_enough_context(context)

    if not should_build:
        answer = _website_planning_reply(context)
        new_history = list(history) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": answer},
        ]
        return answer, new_history

    result = website_builder_create_website(context)
    answer = str(result)
    new_history = list(history) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": answer},
    ]
    return answer, new_history


# ---------------------------------------------------------------------------
# General workspace tools
# ---------------------------------------------------------------------------

def edit_file(filename: str, content: str) -> str:
    return str(fm_edit_file(filename, content))


def search_files(query: str, path: str = ".") -> str:
    root = Path(__file__).resolve().parent.parent / "workspace"
    target = (root / path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return "Search path must stay inside the Shaqs workspace."
    if not target.exists():
        return f"Path does not exist: {target}"
    query = str(query or "").strip().lower()
    if not query:
        return "Search query was empty."
    matches = []
    ignored = {".venv", "__pycache__", ".git"}
    for file in target.rglob("*"):
        if not file.is_file() or any(part in ignored for part in file.parts) or file.name == "memory.db":
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if query in text.lower():
            snippets = [f"{i}: {line.strip()[:180]}" for i, line in enumerate(text.splitlines(), 1) if query in line.lower()][:5]
            matches.append(f"{file.relative_to(root)}\n" + "\n".join(f"  {s}" for s in snippets))
    return "\n".join(matches) if matches else f'No files containing "{query}" were found.'


def delete_path(path: str) -> str:
    root = (Path(__file__).resolve().parent.parent / "workspace").resolve()
    target = (root / str(path)).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return "Path must stay inside the Shaqs workspace."
    if target == root or target == (Path(__file__).resolve().parent.parent / "memory.db").resolve():
        return "Refused to delete a protected Shaqs path."
    if not target.exists():
        return f"Path not found: {target}"
    if target.is_dir():
        import shutil
        shutil.rmtree(target)
        return f"Folder deleted: {target}"
    target.unlink()
    return f"File deleted: {target}"


# ---------------------------------------------------------------------------
# Ollama tool definitions
# ---------------------------------------------------------------------------

tools = [
    {"type": "function", "function": {"name": "get_time", "description": "Get the current local computer time.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "create_file", "description": "Create a file inside the Shaqs workspace.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename"]}}},
    {"type": "function", "function": {"name": "create_folder", "description": "Create a folder inside the Shaqs workspace.", "parameters": {"type": "object", "properties": {"foldername": {"type": "string"}}, "required": ["foldername"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files in the Shaqs workspace.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "read_file", "description": "Read a file in the Shaqs workspace.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}}},
    {"type": "function", "function": {"name": "edit_file", "description": "Replace the contents of an existing workspace file.", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "content": {"type": "string"}}, "required": ["filename", "content"]}}},
    {"type": "function", "function": {"name": "search_files", "description": "Search text inside workspace files.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "path": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "delete_path", "description": "Delete a workspace file or folder safely.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "save_memory", "description": "Save useful long-term information. Use the complete fact as memory.", "parameters": {"type": "object", "properties": {"memory": {"type": "string"}}, "required": ["memory"]}}},
    {"type": "function", "function": {"name": "get_memory", "description": "Retrieve saved long-term memories.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "forget_memory", "description": "Forget saved memories matching supplied text.", "parameters": {"type": "object", "properties": {"memory": {"type": "string"}}, "required": ["memory"]}}},
]


tool_functions = {
    "get_time": get_time,
    "create_file": create_file,
    "create_folder": create_folder,
    "list_files": list_files,
    "read_file": read_file,
    "edit_file": edit_file,
    "search_files": search_files,
    "delete_path": delete_path,
    "save_memory": save_memory,
    "get_memory": get_memory,
    "forget_memory": forget_memory,
}


def normalize_arguments(tool_name: str, arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}
    args = dict(arguments)
    if tool_name in {"save_memory", "forget_memory"} and "memory" not in args:
        if args.get("key") is not None and args.get("value") is not None:
            args["memory"] = f"{args['key']}: {args['value']}"
        elif args.get("value") is not None:
            args["memory"] = args["value"]
        elif args.get("key") is not None:
            args["memory"] = args["key"]
        args = {"memory": args.get("memory", "")}
    return args


def parse_tool_requests(response: Any) -> list[tuple[str, dict[str, Any]]]:
    requests: list[tuple[str, dict[str, Any]]] = []
    official = getattr(response.message, "tool_calls", None) or []
    for call in official:
        args = call.function.arguments
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        requests.append((call.function.name, args if isinstance(args, dict) else {}))
    if requests:
        return requests

    content = str(getattr(response.message, "content", "") or "").strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I | re.S).strip()
    if not content:
        return []
    try:
        parsed = json.loads(content)
        objects = parsed if isinstance(parsed, list) else [parsed]
        for item in objects:
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                args = item.get("arguments", {})
                requests.append((item["name"], args if isinstance(args, dict) else {}))
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            try:
                obj, end = decoder.raw_decode(content, pos)
            except json.JSONDecodeError:
                break
            pos = end
            if isinstance(obj, dict) and isinstance(obj.get("name"), str):
                args = obj.get("arguments", {})
                requests.append((obj["name"], args if isinstance(args, dict) else {}))
    return requests


def parse_tool_request(response: Any):
    requests = parse_tool_requests(response)
    return requests[0] if requests else (None, {})


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    function = tool_functions.get(tool_name)
    if not function:
        return f"Unknown tool: {tool_name}"
    try:
        args = normalize_arguments(tool_name, arguments)
        return str(function(**args))
    except Exception as exc:
        return f"Tool error: {exc}"


def build_system_prompt() -> str:
    memories = get_memories()
    prompt = """You are Shax, a personal voice-enabled AI assistant.
Your replies may be read aloud, so keep them short and conversational unless the user asks for detail.
Be helpful, honest, concise, and practical.
Use tools when they are genuinely needed and trust actual tool results.
Never claim a tool succeeded if its result says it failed.

MEMORY RULES:
- Save long-term facts only when the user explicitly asks you to remember/save/store them.
- Never invent memories.
- Use get_memory when the user asks what you remember.
- Use forget_memory when explicitly asked to forget a memory.

WEBSITE RULE:
Website generation is handled by a deterministic website builder. Do not generate website HTML yourself when the create-website flow is active.
"""
    if memories:
        prompt += "\nLONG-TERM MEMORIES:\n" + "\n".join(f"- {m}" for m in memories)
    return prompt


def _generic_chat(user_message: str, history: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    available_tools = list(tools)

    explicit_memory = any(x in user_message.lower() for x in ("remember this", "remember that", "save this", "save that", "store this", "store that"))
    memory_question = any(x in user_message.lower() for x in ("what do you remember", "show my memories", "list my memories", "my memories"))
    forget_question = any(x in user_message.lower() for x in ("forget this", "forget that", "delete this memory", "remove this memory"))
    if not explicit_memory:
        available_tools = [t for t in available_tools if t["function"]["name"] != "save_memory"]
    if not memory_question:
        available_tools = [t for t in available_tools if t["function"]["name"] != "get_memory"]
    if not forget_question:
        available_tools = [t for t in available_tools if t["function"]["name"] != "forget_memory"]

    last_results: list[str] = []
    for _ in range(8):
        try:
            response = _ollama_chat(model=MODEL, messages=messages, tools=available_tools)
        except Exception as exc:
            answer = f"Shaqs error: {exc}"
            return answer, history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]

        requests = parse_tool_requests(response)
        if requests:
            if getattr(response.message, "tool_calls", None):
                messages.append(response.message)
            else:
                messages.append({"role": "assistant", "content": getattr(response.message, "content", "") or ""})
            for tool_name, arguments in requests:
                result = execute_tool(tool_name, arguments)
                last_results.append(f"{tool_name}: {result}")
                messages.append({"role": "tool", "content": result})
            continue

        answer = str(getattr(response.message, "content", "") or "").strip()
        if not answer:
            answer = "\n".join(last_results) if last_results else "I completed the request, but the model returned no text."
        return answer, history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]

    answer = "Tool execution reached the safety limit.\n\n" + "\n".join(last_results)
    return answer, history + [{"role": "user", "content": user_message}, {"role": "assistant", "content": answer}]


def run_agent(user_message: str, conversation: list[dict[str, Any]] | None = None):
    history = [m for m in (conversation or []) if isinstance(m, dict) and m.get("role") in {"user", "assistant", "tool"}]
    website_result = _handle_website_request(str(user_message), history)
    if website_result is not None:
        return website_result
    return _generic_chat(str(user_message), history)
