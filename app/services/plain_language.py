"""Return fixed plain wording; never let a language model reinterpret findings.

plain_findings.json pairs each exact source sentence with its plain version by
language and finding key. Preserve findings without a matching entry, including
dynamic symptom/surgery text. If the frontend source changes, it must be reviewed
alongside the plain version before the entry is updated; no fuzzy matching.
"""
import json
from pathlib import Path

_CATALOG = json.loads(Path(__file__).with_name("plain_findings.json").read_text(encoding="utf-8"))
_BY_LANGUAGE = {
    lang: {entry["original"]: entry["plain"] for entry in entries.values()}
    for lang, entries in _CATALOG.items()
}


async def rewrite_findings(lines: list[str], lang: str) -> list[dict]:
    """Keep the existing API shape; unknown sources/languages remain unchanged."""
    wording = _BY_LANGUAGE.get(lang, {})
    return [
        {"text": wording.get(line, line), "rewritten": line in wording and wording[line] != line}
        for line in lines
    ]
