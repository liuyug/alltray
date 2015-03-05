#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os
import sys
import subprocess

from distutils.core import setup
from distutils.command import install_scripts

from alltray import __version__


class post_install_scripts(install_scripts.install_scripts):
    """ remove script ext """
    def run(self):
        install_scripts.install_scripts.run(self)
        for script in self.get_outputs():
            if script.endswith(".py"):
                new_name = script[:-3]
                if os.path.exists(new_name):
                    os.remove(new_name)
                print('renaming %s -> %s' % (script, new_name))
                os.rename(script, new_name)
                cmd = ['sed', '-i', '-r', 's/Exec=.*$/Exec=%s/' % new_name.replace('/', '\/'), 'alltray.desktop']
                print(' '.join(cmd))
                subprocess.call(cmd)
        return

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
      scripts=['alltray.py'],
      packages=[
          'alltray',
      ],
      requires=['pyqt4'],
      data_files=data_files,
      cmdclass={
          'install_scripts': post_install_scripts,
      },
      )
