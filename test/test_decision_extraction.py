# tests/test_match_conflict_url.py
import pytest

# Update this import to your actual module path
# e.g. from services.integration.disambiguation.matching import match_conflict_url
from human_annotations.scripts.extract_decision import match_conflict_url


def _render_issue_body(conflict_id: str, conflict_url: str) -> str:
    """
    Minimal issue body matching the start of your Jinja template, plus some extra content.
    """
    return f"""> This issue was created automatically by the metadata disambiguation pipeline because the associated block could not be resolved with high confidence.
> Conflict Id: {conflict_id}
> Conflict File: [{conflict_url}]({conflict_url})

A conflict has been detected between two software metadata entries with the same name but no shared repository or website. Please review the metadata and provide your decision using the format below.

**Annotation Guidelines**: refer to the [annotation guidelines](https://link-to-guidelines.example.com) if needed. 

---

### Entry A - Some Tool

- **Name**: Some Tool
- **ID**: entry-a-123
"""


@pytest.mark.parametrize(
    "body_builder, expected_url",
    [
        # Canonical: markdown link exactly as template emits
        (
            lambda: _render_issue_body(
                conflict_id="abc123",
                conflict_url="https://github.com/org/repo/blob/main/human_annotations/conflicts/conflict_abc123.json",
            ),
            "https://github.com/org/repo/blob/main/human_annotations/conflicts/conflict_abc123.json",
        ),
        # Windows newlines (\r\n) - common when content gets normalized across systems
        (
            lambda: _render_issue_body(
                conflict_id="abc123",
                conflict_url="https://example.com/conflicts/conflict_abc123.json",
            ).replace("\n", "\r\n"),
            "https://example.com/conflicts/conflict_abc123.json",
        ),
        # Trailing spaces at end of the "Conflict File" line
        (
            lambda: _render_issue_body(
                conflict_id="abc123",
                conflict_url="https://example.com/conflicts/conflict_abc123.json",
            ).replace(
                f"> Conflict File: [https://example.com/conflicts/conflict_abc123.json](https://example.com/conflicts/conflict_abc123.json)",
                f"> Conflict File: [https://example.com/conflicts/conflict_abc123.json](https://example.com/conflicts/conflict_abc123.json)   ",
            ),
            "https://example.com/conflicts/conflict_abc123.json",
        )
    ],
)
def test_match_conflict_url_extracts_conflict_file_url(body_builder, expected_url):
    body = body_builder()
    assert match_conflict_url(body) == expected_url


def test_match_conflict_url_returns_none_when_missing():
    body = """> This issue was created automatically...
> Conflict Id: abc123

No conflict file line here.
"""
    assert match_conflict_url(body) is None