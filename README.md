# Shax — voice-assisted personal AI agent

## One-step install (Windows PowerShell)
```
powershell -ExecutionPolicy Bypass -File install.ps1
```

## Quick start (Windows, manual)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-voice.txt
ollama pull qwen2.5-coder:7b
python main.py --voice
```
Then say: **"Shax, what time is it?"** or **"Shax, build a website for a garage called Royal Car Service."**

- `python main.py` — text mode
- `python main.py --voice` — voice mode, responds when you say "Shax"
- `python main.py --voice --always-listen` — responds to everything you say
- Say "goodbye" (or press Ctrl+C) to quit.

Voice uses Google's free web speech recognition by default. For fully offline, private
recognition: `pip install openai-whisper` (also needs ffmpeg). Spoken replies use pyttsx3 (offline).
If PyAudio fails to install, try `pip install pipwin && pipwin install pyaudio`.

---

# Shaqs — stable engineering + visual quality pass

This build preserves the working Shaqs architecture and improves the website generator's visual system without rebuilding the agent or tool architecture.

## Changed in this pass
- `skills/website_builder.py`
  - stronger visual hierarchy and spacing
  - more polished navigation/header
  - clearer CTA styling and focus states
  - richer depth using restrained gradients, borders, glows and layered panels
  - category-specific visual personality remains intact
  - customer-facing hero personality cues instead of design-system commentary
  - improved card composition and hover states
  - improved About and final CTA sections
  - accessible mobile navigation
  - safer animation strategy: content is visible without JavaScript and animations respect reduced-motion preferences
  - removed the previous scroll-triggered hidden-content behavior that could leave large portions of the page invisible in captures/initial rendering
  - preserved single-file HTML, inline CSS, inline SVG and vanilla JavaScript
- `tests/test_project.py`
  - added regression coverage for the exact `build a modern website for a coffee shop called kimshi` request
  - added checks for the new visual output not containing the old unfinished contact placeholder

## Visual direction
The generator still uses genuinely different layout families:
- coffee — editorial
- automotive — industrial
- restaurant — culinary
- salon — luxury
- fitness — athletic
- retail — bento
- professional — structured
- creative/portfolio requests — portfolio
- other requests — modular

The design system changes geometry, spacing, panel treatment, card composition, hierarchy and visual language by category rather than simply swapping colors.

## Quality checks performed for this pass
- Python compilation: PASS
- Existing project tests: PASS
- Exact `kimshi` request regression: PASS
- Eight category/style rendering cases: PASS
- Desktop, tablet and mobile browser rendering checks: PASS
- Mobile navigation open/close interaction: PASS
- No horizontal overflow in tested viewports: PASS
- No browser console errors in tested pages: PASS
- Self-contained HTML validation: PASS
- No external assets, URLs, images, iframes, audio/video or external stylesheets: PASS
- Final generated pages contain the core Hero / Offer / About / Contact structure: PASS

Live Ollama inference is optional and remains lazy-loaded. When Ollama is unavailable, deterministic category-specific fallback copy keeps website generation functional.
