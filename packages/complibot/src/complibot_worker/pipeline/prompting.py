"""Prompt helpers for worker LLM calls."""


def wrap_document(text: str) -> str:
    """Escape tag-like sequences so document content cannot break delimiters."""
    escaped = (
        text.replace("&", "&amp;")
        .replace("<document_text", "&lt;document_text")
        .replace("</document_text>", "&lt;/document_text&gt;")
    )
    return f'<document_text trust="untrusted">\n{escaped}\n</document_text>'
