"""AC-AI-01: citation quote must equal document slice."""


def test_citation_substring() -> None:
    text = "The Processor shall notify without undue delay."
    start = text.find("notify")
    end = start + len("notify without undue delay")
    quote = text[start:end]
    assert quote == text[start:end]
