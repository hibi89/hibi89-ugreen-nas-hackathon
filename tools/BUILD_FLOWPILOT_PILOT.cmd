@echo off
setlocal
REM Build tested self-contained LOCAL pilot ZIP; no private NAS sources/data.
set "OUT=%~dp0..\FlowPilot_Local_Pilot.zip"
py -3.11 "%~dp0build_flowpilot_pilot_zip.py" --out "%OUT%"
if errorlevel 1 (
  echo Local pilot ZIP build refused or acceptance failed.
  pause
  exit /b 2
)
echo Self-contained local pilot ZIP created after 4-capability acceptance.
pause
