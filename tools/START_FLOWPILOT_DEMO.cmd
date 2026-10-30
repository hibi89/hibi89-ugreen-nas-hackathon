@echo off
setlocal
REM UGREEN FlowPilot: real OS filesystem demo, no private HAE/DBVORA/NAS needed.
REM Runs on localhost only and opens the browser. Close this window to stop.
py -3.11 "%~dp0flowpilot_four_source_local_ui.py" --open-browser
if errorlevel 1 (
  echo Local demo could not start. Python 3.11 and py launcher are required.
  pause
)
