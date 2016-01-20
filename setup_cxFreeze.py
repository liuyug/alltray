#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys
import plistlib

from cx_Freeze import setup, Executable

from alltray import __version__

plist = {
    'CFBundleShortVersionString': __version__,
    'CFBundleSignature': 'ALLT',
    'CFBundleInfoDictionaryVersion': '6.0',
    'CFBundleDisplayName': 'AllTray v%s' % __version__,
    'CFBundleIconFile': 'icon.icns',
    'CFBundleIdentifier': 'alltray.liuyug.com.github',
    'CFBundleDevelopmentRegion': 'en-US',
    'CFBundleExecutable': 'alltray',
    'CFBundleName': 'AllTray',
    'CFBundlePackageType': 'APPL',
    'CFBundleVersion': __version__,
    'NSHumanReadableCopyright': 'GNU GPLv3',
}

include_files = []
include_files.append(['Apps-wheelchair.ico', 'Apps-wheelchair.ico'])
include_files.append(['alltray.desktop', 'alltray.desktop'])

build_exe_options = {
    'include_files': include_files,
}

bdist_mac_options = {
    'iconfile': 'Apps-wheelchair.icns',
    'custom_info_plist': 'Info.plist',
}

bdist_dmg_options = {
}


base = None
options = {}
if sys.platform == "win32":
    base = "Win32GUI"
    options['build_exe'] = build_exe_options
elif sys.platform == 'darwin':
    plistlib.writePlist(plist, 'Info.plist')
    options['bdist_mac'] = bdist_mac_options
    options['bdist_dmg'] = bdist_dmg_options


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
      executables=execute_scripts,
      options=options,
      )
