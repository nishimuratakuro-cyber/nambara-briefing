@echo off
cd /d %~dp0
python generate_briefing.py >> run_log.txt 2>&1
