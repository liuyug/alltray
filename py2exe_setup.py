#!/usr/bin/env python
# -*- encoding:utf-8 -*-

from distutils.core import setup

from alltray import __version__

import os.path
import PyQt4
from glob import glob

try:
    import py2exe
except:
    pass

pyqt_files = [
    (
        'imageformats',
        glob(os.path.join(os.path.dirname(PyQt4.__file__),
                          'plugins', 'imageformats', '*.*'))
    ),
]
py2exe_options = {
    #'skip_archive': True,
    'includes': ['sip'],
    'compressed': 1,
    'optimize': 2,
    # 'bundle_files': 1,
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
      data_files=pyqt_files,
      windows=['alltray.py'],
      options={'py2exe': py2exe_options}
      )
