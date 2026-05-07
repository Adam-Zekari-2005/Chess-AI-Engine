@echo off
cd /d "%~dp0"

where node >nul 2>nul
if %errorlevel%==0 (
  node web\server.js
  exit /b %errorlevel%
)

set "BUNDLED_NODE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
if exist "%BUNDLED_NODE%" (
  "%BUNDLED_NODE%" web\server.js
  exit /b %errorlevel%
)

echo Node.js n'est pas installe ou introuvable.
echo Installe Node.js depuis https://nodejs.org puis relance start_web.bat
exit /b 1
