@echo off

rem pywin32: http://sourceforge.net/projects/pywin32/files/
rem pip install pyinstaller

echo on
pyinstaller --clean --noupx -i Apps-wheelchair.ico -w alltray.py
