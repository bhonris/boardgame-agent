import pytest

from app.services.rulebook_ingestion import chunk_text, detect_sections, extract_text_from_pdf


class TestChunkText:
    def test_single_chunk(self):
        text = "This is a short piece of text about game rules."
        chunks = chunk_text(text, "Introduction", max_tokens=500)
        assert len(chunks) == 1
        assert chunks[0]["section_name"] == "Introduction"
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["chunk_text"] == text

    def test_multiple_chunks(self):
        words = ["word"] * 1000
        text = " ".join(words)
        chunks = chunk_text(text, "Rules", max_tokens=500)
        assert len(chunks) == 2
        assert chunks[0]["chunk_index"] == 0
        assert chunks[1]["chunk_index"] == 1

    def test_empty_text(self):
        chunks = chunk_text("", "Empty", max_tokens=500)
        assert len(chunks) == 0

    def test_whitespace_only(self):
        chunks = chunk_text("   ", "Whitespace", max_tokens=500)
        assert len(chunks) == 0

    def test_token_count(self):
        text = "one two three four five"
        chunks = chunk_text(text, "Test", max_tokens=500)
        assert chunks[0]["token_count"] == 5

    def test_exact_boundary(self):
        words = ["word"] * 500
        text = " ".join(words)
        chunks = chunk_text(text, "Test", max_tokens=500)
        assert len(chunks) == 1
        assert chunks[0]["token_count"] == 500


class TestDetectSections:
    def test_detect_uppercase_headings(self):
        text = "SETUP\nPlace the board on the table.\nGather all pieces.\n\nGAMEPLAY\nRoll the dice.\nMove your piece.\n"
        sections = detect_sections(text)
        names = [s["name"] for s in sections]
        assert "SETUP" in names
        assert "GAMEPLAY" in names

    def test_single_section(self):
        text = "This is just some text without any clear headings. It goes on and on."
        sections = detect_sections(text)
        assert len(sections) >= 1

    def test_empty_text(self):
        sections = detect_sections("")
        assert len(sections) == 0 or all(not s["content"].strip() for s in sections)

    def test_preserves_content(self):
        text = "RULES\nRule one.\nRule two.\n"
        sections = detect_sections(text)
        rules_section = next((s for s in sections if s["name"] == "RULES"), None)
        assert rules_section is not None
        assert "Rule one" in rules_section["content"]
        assert "Rule two" in rules_section["content"]
