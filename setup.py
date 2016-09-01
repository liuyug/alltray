#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os
import sys
import subprocess

from setuptools import setup

from alltray import __version__


data_files = []
if sys.platform in ['linux', 'linux2']:
    data_files.append(('share/applications', ['alltray.desktop']))

setup(name='AllTray',
      version=__version__,
      author='Yugang LIU',
      author_email='liuyug@gmail.com',
      url='https://github.com/liuyug/alltray',
      license='GPLv3',
      description='Tray all application',
      long_description=open('README.rst').read(),
      platforms=['noarch'],
      packages=[
          'alltray',
      ],
      data_files=data_files,
      entry_points={
          'console_scripts': [
              'alltray = alltray.tray:main',
          ],
      },
      zip_safe=False,
      )
