param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment. Install Python 3.12 or 3.13.' }
}
if (-not (Test-Path '.venv/.figuraforge-installed')) {
    & .venv/Scripts/python.exe -m pip install --upgrade pip
    & .venv/Scripts/python.exe -m pip install -c requirements-tested.txt -e .
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    New-Item -ItemType File '.venv/.figuraforge-installed' -Force | Out-Null
}
& .venv/Scripts/python.exe scripts/run.py --port $Port
