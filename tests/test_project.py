from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skills.website_builder import (  # noqa: E402
    detect_category,
    extract_name,
    get_design_strategy,
    render,
    validate_website_html,
    _fallback_plan,
)


def test_parser() -> None:
    cases = [
        ("Build a website for a coffee shop named KOPIEEE.", "KOPIEEE", "coffee"),
        ("Build a modern website for a coffee shop called kimshi.", "kimshi", "coffee"),
        ("Build a website for Royal Car Service, an automotive garage.", "Royal Car Service", "automotive"),
        ("Build a website for a fitness gym called Titan Fitness.", "Titan Fitness", "fitness"),
        ("Create a website for a restaurant called Ember Table.", "Ember Table", "restaurant"),
        ("Create a website for KOPIEEE. IMPORTANT CONTEXT RULE = IGNORE unrelated previous website projects.", "KOPIEEE", "general"),
    ]
    # The last request intentionally has no category word. The parser should not
    # invent a category, but it must still extract the correct name.
    for request, expected_name, expected_category in cases:
        category = detect_category(request)
        name = extract_name(request, category)
        assert name == expected_name, (name, expected_name)
        if expected_category != "general":
            assert category == expected_category, (category, expected_category)


def test_layouts_and_validation() -> None:
    requests = [
        ("coffee", "KOPIEEE"),
        ("automotive", "Royal Car Service"),
        ("restaurant", "Ember Table"),
        ("salon", "Velvet Studio"),
        ("fitness", "Titan Fitness"),
        ("retail", "Northline"),
        ("professional", "ClearPath"),
    ]
    layouts = set()
    for category, name in requests:
        strategy = get_design_strategy(category, f"Build a website for a {category} called {name}.")
        layouts.add(strategy["template"])
        html = render(_fallback_plan(category, name), name, category)
        ok, error = validate_website_html(html)
        assert ok, error
    assert len(layouts) >= 7, layouts
    modern = render(_fallback_plan("coffee", "kimshi"), "kimshi", "coffee", "Build a modern website for a coffee shop called kimshi.")
    assert "When real contact" not in modern
    assert "Warm editorial" in modern
    assert "background-image" not in modern.lower()


def test_self_contained_rules() -> None:
    html = render(_fallback_plan("coffee", "KOPIEEE"), "KOPIEEE", "coffee")
    lower = html.lower()
    for forbidden in ("<img", "<iframe", "background-image", "url(", "<link", "@import"):
        assert forbidden not in lower
    assert "http://" not in lower
    assert "https://" not in lower


if __name__ == "__main__":
    test_parser()
    test_layouts_and_validation()
    test_self_contained_rules()
    print("All Shaqs project tests passed.")
