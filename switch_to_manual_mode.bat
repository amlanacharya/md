@echo off
echo Switching to MANUAL mode...
python fix_workflow_mode.py manual
echo.
echo Verifying the change:
python check_db_workflow_mode.py
pause
