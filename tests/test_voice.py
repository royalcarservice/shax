from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from skills.voice import is_stop_command, make_speakable, strip_wake_word  # noqa: E402


def test_wake_word() -> None:
    assert strip_wake_word("Hey Shax, what time is it?") == (True, "what time is it?")
    assert strip_wake_word("shaqs build a website for a gym called Titan") == (True, "build a website for a gym called Titan")
    assert strip_wake_word("Shax") == (True, "")
    assert strip_wake_word("what time is it") == (False, "what time is it")
    assert strip_wake_word("saxophone lessons")[0] is False


def test_stop() -> None:
    assert is_stop_command("Goodbye.")
    assert is_stop_command("stop listening")
    assert not is_stop_command("goodbye message for my site")


def test_speakable() -> None:
    spoken = make_speakable(r"Website created successfully at: C:\Users\me\Shaqs\workspace\websites\shaqs_website.html")
    assert spoken == "Website created successfully at: shaqs website.html", spoken
    assert "<div>" not in make_speakable("<div>Hello</div>")
    long = make_speakable("This is a sentence. " * 100)
    assert len(long) < 700 and long.endswith("The rest is on screen.")


if __name__ == "__main__":
    test_wake_word()
    test_stop()
    test_speakable()
    print("All voice tests passed.")
