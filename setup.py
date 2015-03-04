#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import os

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
        return


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
      cmdclass={
          'install_scripts': post_install_scripts,
      }
      )
