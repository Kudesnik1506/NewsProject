"""Shared utilities for JSON/text extraction from Claude responses."""
import json
import re
from pathlib import Path


def _resolve_includes(text: str, agents_dir: Path) -> str:
    """Replace {{include: filename.md}} directives with the full content of the referenced file."""
    def replacer(match):
        filename = match.group(1).strip()
        included_path = agents_dir / filename
        if not included_path.exists():
            raise FileNotFoundError(f"Included file not found: {included_path}")
        return included_path.read_text(encoding="utf-8").strip()

    return re.sub(r"\{\{include:\s*([^}]+)\}\}", replacer, text)


def load_prompt(agent_name: str) -> str:
    """Load system prompt from the '## System prompt' section of agents/{agent_name}.md.

    Supports {{include: filename.md}} directives — the referenced file content is inlined.
    """
    agents_dir = Path(__file__).parent.parent / "agents"
    md_path = agents_dir / f"{agent_name}.md"
    text = md_path.read_text(encoding="utf-8")
    match = re.search(r"## System prompt\n+(.*?)\n+---\n+## User prompt", text, re.DOTALL)
    if not match:
        raise ValueError(f"'## System prompt' section not found in {md_path}")
    return _resolve_includes(match.group(1).strip(), agents_dir)


def load_user_prompt(agent_name: str, section: str = "default") -> str:
    """Load user prompt template from the '## User prompt' section of agents/{agent_name}.md.

    section="default" — matches the first '## User prompt' heading (any form).
    section="full"    — matches '## User prompt (full)' specifically.
    section="fast"    — matches '## User prompt (fast)' specifically.

    Supports {{include: filename.md}} directives — the referenced file content is inlined.
    """
    agents_dir = Path(__file__).parent.parent / "agents"
    md_path = agents_dir / f"{agent_name}.md"
    text = md_path.read_text(encoding="utf-8")

    if section == "default":
        pattern = r"## User prompt[^\n]*\n+```[^\n]*\n(.*?)```"
    else:
        pattern = rf"## User prompt \({re.escape(section)}\)[^\n]*\n+```[^\n]*\n(.*?)```"

    match = re.search(pattern, text, re.DOTALL)
    if not match:
        raise ValueError(f"'## User prompt ({section})' section not found in {md_path}")
    return _resolve_includes(match.group(1).strip(), agents_dir)


def extract_json(text: str):
    """Extract JSON from Claude response, handling markdown code blocks."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` or ``` ... ``` blocks (greedy — capture up to last ```)
    match = re.search(r"```(?:json)?\s*([\s\S]*)\s*```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try finding first [ or { and parsing from there
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract JSON from response:\n{text[:300]}")


def extract_text(text: str) -> str:
    """Strip markdown code fences if the entire response is wrapped in them."""
    text = text.strip()
    match = re.match(r"```(?:markdown)?\s*([\s\S]*?)\s*```$", text)
    if match:
        return match.group(1).strip()
    return text
