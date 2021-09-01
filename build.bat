title=building
@echo off
pyinstaller -F --noupx -i static/img/data.ico .\app.py
pause
exit