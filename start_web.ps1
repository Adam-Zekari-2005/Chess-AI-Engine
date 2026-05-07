$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$serverPath = Join-Path $projectRoot "web\server.js"
$bundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue

Set-Location $projectRoot

if ($nodeCommand) {
    & $nodeCommand.Source $serverPath
    exit $LASTEXITCODE
}

if (Test-Path $bundledNode) {
    & $bundledNode $serverPath
    exit $LASTEXITCODE
}

Write-Host "Node.js n'est pas installe ou introuvable."
Write-Host "Installe Node.js depuis https://nodejs.org puis relance: .\start_web.ps1"
exit 1
