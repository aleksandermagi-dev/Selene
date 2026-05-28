@echo off
setlocal
cd /d "%~dp0\.."
python -m pip install -e .[packaging]
pyinstaller selene_sidecar.spec --distpath dist-sidecar --workpath build-sidecar --noconfirm
