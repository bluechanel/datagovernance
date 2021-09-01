title=building
@echo off
pyinstaller --clean -y -F --noupx -i static/img/data.ico .\app.py --add-data "static;static" --add-data "templates;templates
pause
exit