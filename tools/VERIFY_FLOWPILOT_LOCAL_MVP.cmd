@echo off
setlocal
REM Four real local capabilities; synthetic disposable test data ONLY.
REM No NAS, Uliya, customer files or external API.
py -3.11 "%~dp0flowpilot_local_acceptance.py"
if errorlevel 1 (
  echo LOCAL ACCEPTANCE FAILED. Do not mark NAS or private integrations passed.
  pause
  exit /b 2
)
echo Four local capabilities verified on synthetic disposable data.
pause
