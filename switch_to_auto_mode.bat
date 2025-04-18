@echo off
echo Switching to AUTO mode...
python fix_workflow_mode.py auto
echo.
echo Verifying the change:
python check_db_workflow_mode.py
pause
