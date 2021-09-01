title=building
@echo off
pyinstaller --clean -y -i static/img/data.ico -n governance .\app.py --add-data "static;static" --add-data "templates;templates" --add-data "data;data"
pause
exit