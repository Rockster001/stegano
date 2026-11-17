@echo off
cd /d C:\Dev\Stegano
aider --model zai/glm-4.5-flash --no-auto-commits Stegano.py steganography_utils.py ui_components.py
pause
