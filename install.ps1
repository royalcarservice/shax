# Shax installer for Windows. Run in PowerShell from the folder that contains (or will contain) shax.
$ErrorActionPreference = "Stop"

function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

Write-Host "== 1/5 Installing Git, Python and Ollama (skips anything already installed)" -ForegroundColor Cyan
if (-not (Have git))    { winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements }
if (-not (Have python)) { winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements }
if (-not (Have ollama)) { winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements }
Refresh-Path

Write-Host "== 2/5 Getting the Shax code" -ForegroundColor Cyan
if (Test-Path ".\main.py") {
    git pull
} elseif (Test-Path ".\shax\main.py") {
    Set-Location shax; git pull
} else {
    git clone -b claude/zealous-bell-rs9zg8 https://github.com/royalcarservice/shax.git
    Set-Location shax
}

Write-Host "== 3/5 Creating the Python environment" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt SpeechRecognition pyttsx3
try {
    & $py -m pip install PyAudio
} catch {
    Write-Host "PyAudio failed, trying pipwin..." -ForegroundColor Yellow
    & $py -m pip install pipwin
    & $py -m pipwin install pyaudio
}

Write-Host "== 4/5 Downloading the AI model (about 4.7 GB, one time only)" -ForegroundColor Cyan
ollama pull qwen2.5-coder:7b

Write-Host "== 5/5 Checking everything works" -ForegroundColor Cyan
& $py tests\test_voice.py
& $py tests\test_project.py

Write-Host ""
Write-Host "Shax is installed. Starting voice mode - say 'Shax, what time is it?'" -ForegroundColor Green
& $py main.py --voice
