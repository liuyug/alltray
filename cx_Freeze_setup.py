#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys

from cx_Freeze import setup, Executable

from alltray import __version__

base = None
if sys.platform == "win32":
    base = "Win32GUI"

build_exe_options = {
}

bdist_mac_options = {
    'iconfile': 'Apps-wheelchair.icns',
}

bdist_dmg_options = {
}

execute_scripts = [
    Executable(script='alltray.py', icon='Apps-wheelchair.ico', base=base)
]

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
      executables=execute_scripts,
      options={
          'build_exe': build_exe_options,
          'bdist_mac': bdist_mac_options,
          'bdist_dmg': bdist_dmg_options,
      }
      )
