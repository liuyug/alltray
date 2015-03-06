#!/bin/sh

pyinstaller="/opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/pyinstaller"

$pyinstaller --clean --noupx -i Apps-wheelchair.icns -w -F alltray.py
