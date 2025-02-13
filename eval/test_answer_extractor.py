import pytest

from eval.answer_extractor import regex_extract_answer


@pytest.mark.parametrize(
    "output, expected_answer",
    [
        ("ANSWER: **42**", 42),  # Bold formatting
        ("ANSWER:  **  3.14  **!", 3.14),  # Bold with extra spaces and punctuation
        ("The problem is solved. ANSWER:  123   ", 123),  # Extra spaces
        ("ANSWER: _even_", "even"),  # Italic formatting
        ("ANSWER: **neither**!", "neither"),  # Bold with punctuation
        ("ANSWER: none", "none"),  # Lowercase 'none'
        ("No explicit answer here.", None),  # No answer present
        ("ANSWER: **-7**", -7),  # Negative integer with bold formatting
        ("ANSWER:  **  0  **", 0),  # Zero
        ("ANSWER: 12.0", 12.0),  # Float without special formatting
        ("**ANSWER**: 3.14", 3.14),  # Bold formatting at the start
        ("### ANSWER:\nTrue", True),  # Markdown heading
        ("ANSWER: True.", True),  # True with punctuation
    ],
)
def test_regex_extract_answer(output, expected_answer):
    assert regex_extract_answer(output) == expected_answer
