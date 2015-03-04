#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys

from cx_Freeze import setup, Executable

from alltray import __version__

base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = {
    'icon': 'Apps-wheelchair.ico',
}

setup(name='AllTray',
      version=__version__,
      author='Yugang LIU',
      author_email='liuyug@gmail.com',
      url='https://github.com/liuyug/alltray',
      license='GPLv3',
      description='Tray all application',
      platforms=['noarch'],
      scripts=['alltray.py'],
      packages=[
          'alltray',
      ],
      requires=['pyqt4'],
      executables=[Executable('alltray.py', base=base)],
      options={'build_exe': build_exe_options}
      )
