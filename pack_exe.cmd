
cls

pyinstaller --clean --onefile --noconfirm --noconsole --name alltray --icon "Apps-wheelchair.ico" --hidden-import PyQt5.sip run.py

rmdir build /s /q
del alltray.spec

rem fix pyinstaller bug
xcopy C:\Python36\Lib\site-packages\PyQt5\Qt\plugins\styles  dist\alltray\PyQt5\Qt\plugins\styles\ /d
copy Apps-wheelchair.ico dist\alltray
copy Apps-wheelchair.icns dist\alltray

