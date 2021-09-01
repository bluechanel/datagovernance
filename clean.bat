title=cleaning
@echo off
rmdir /s /q __pycache__
echo  - %cd%\__pycache__
rmdir /s /q build
echo  - %cd%\build
rmdir /s /q dist
echo  - %cd%\dist
del /f /s /q *.spec
pause
exit