"""Voice input/output for Shax.

Speech-to-text: SpeechRecognition + microphone (PyAudio).
    - Uses local Whisper if `openai-whisper` is installed (offline, private).
    - Otherwise falls back to Google's free web recognizer (needs internet).
Text-to-speech: pyttsx3 (offline; uses Windows SAPI5 / macOS NSSpeech / espeak).

Every audio library is imported lazily so the rest of Shax (and the tests)
work on machines without a microphone or the voice packages installed.
"""

from __future__ import annotations

import re

WAKE_WORDS = ("shax", "shaqs", "shacks", "shaq", "shax's", "shocks", "jacks", "sax")
STOP_PHRASES = {"exit", "quit", "goodbye", "stop listening", "shut down", "go to sleep"}

_MAX_SPOKEN_CHARS = 600


# ---------------------------------------------------------------------------
# Pure text helpers (no audio dependencies — unit tested)
# ---------------------------------------------------------------------------

def strip_wake_word(text: str) -> tuple[bool, str]:
    """Return (woke, command) where command has the leading wake word removed.

    "Hey Shax, what time is it" -> (True, "what time is it")
    "what time is it"           -> (False, "what time is it")
    """
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    pattern = r"^(?:(?:hey|hi|ok|okay|yo)\s+)?(?:" + "|".join(map(re.escape, WAKE_WORDS)) + r")\b[\s,.:!?-]*"
    match = re.match(pattern, cleaned, flags=re.I)
    if not match:
        return False, cleaned
    return True, cleaned[match.end():].strip()


def is_stop_command(text: str) -> bool:
    return re.sub(r"[^\w\s]", "", str(text or "").lower()).strip() in STOP_PHRASES


def make_speakable(text: str) -> str:
    """Turn an agent response into something pleasant to hear."""
    value = str(text or "")
    value = re.sub(r"```.*?```", " I've put the code on screen. ", value, flags=re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    # Read file paths as just their file name.
    value = re.sub(r"(?:[A-Za-z]:)?[\\/](?:[^\s\\/]+[\\/])+([^\s\\/]+)", r"\1", value)
    value = re.sub(r"https?://\S+", "a link", value)
    value = re.sub(r"[*#_`>|=]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) > _MAX_SPOKEN_CHARS:
        cut = value[:_MAX_SPOKEN_CHARS]
        cut = cut[: max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? ")) + 1] or cut
        value = cut.strip() + " The rest is on screen."
    return value


# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------

class VoiceUnavailable(RuntimeError):
    pass


class Voice:
    def __init__(self, rate: int = 185, energy_threshold: int | None = None):
        try:
            import speech_recognition as sr  # type: ignore
        except ImportError as exc:
            raise VoiceUnavailable(
                "Voice needs extra packages. Run: pip install -r requirements-voice.txt"
            ) from exc
        self._sr = sr
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = energy_threshold is None
        if energy_threshold is not None:
            self.recognizer.energy_threshold = energy_threshold
        try:
            self.microphone = sr.Microphone()
        except Exception as exc:  # PyAudio missing or no input device
            raise VoiceUnavailable(f"No microphone available ({exc}). Install PyAudio and check your mic.") from exc

        self._rate = rate
        self._tts = None
        self._use_whisper = self._has_whisper()
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    @staticmethod
    def _has_whisper() -> bool:
        try:
            import whisper  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False

    @property
    def engine_name(self) -> str:
        return "Whisper (offline)" if self._use_whisper else "Google web speech (online)"

    def speak(self, text: str) -> None:
        spoken = make_speakable(text)
        if not spoken:
            return
        try:
            if self._tts is None:
                import pyttsx3  # type: ignore
                self._tts = pyttsx3.init()
                self._tts.setProperty("rate", self._rate)
            self._tts.say(spoken)
            self._tts.runAndWait()
        except Exception as exc:
            print(f"(voice output unavailable: {exc})")

    def listen(self, timeout: float | None = None, phrase_time_limit: float = 20) -> str:
        """Record one phrase and return its transcript ('' if nothing understood)."""
        sr = self._sr
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except sr.WaitTimeoutError:
                return ""
        try:
            if self._use_whisper:
                return self.recognizer.recognize_whisper(audio, model="base", language="english").strip()
            return self.recognizer.recognize_google(audio).strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as exc:
            print(f"(speech service error: {exc})")
            return ""
