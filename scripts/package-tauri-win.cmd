@echo off
setlocal
cd /d "%~dp0\.."
call npm run build
call scripts\build-python-sidecar.cmd
call npm run tauri:build
