#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys
import subprocess
import threading
import locale
import argparse
import shlex
import os.path
from functools import partial

from PyQt5 import QtGui, QtCore, QtWidgets
import psutil

from alltray import __version__


class TrayDialog(QtWidgets.QDialog):
    logThread = None

    def __init__(self, settings, parent=None):
        super(TrayDialog, self).__init__(parent)
        self.settings = settings
        self.setWindowTitle(self.tr('All Tray'))

    def create(self):
        # widgets
        self.settingWidget = self.getSettingWidget()
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Apply | QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.applyCommand)
        # layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self.settingWidget)
        main_layout.addWidget(self.buttonBox)
        self.setLayout(main_layout)

        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setContextMenu(self.getMenu())
        self.tray.setIcon(self.windowIcon())
        self.tray.setToolTip(self.general_ctl.tooltip.text())
        self.tray.activated.connect(self.trayActivated)

        if self.general_ctl.app_run.isChecked():
            self.tray.show()

    def getSettingWidget(self):
        tabWidget = QtWidgets.QTabWidget(self)
        self.general_ctl = GeneralWidget(tabWidget, self.settings)
        self.log_ctl = LogWidget(tabWidget)
        # about diaglog
        self.aboutDlg = QtWidgets.QDialog(self)
        about = AboutWidget(self.aboutDlg)
        about_layout = QtWidgets.QVBoxLayout()
        about_layout.addWidget(about)
        about_layout.addStretch(1)
        self.aboutDlg.setLayout(about_layout)
        # add tab
        tabWidget.addTab(self.general_ctl, self.tr('General'))
        tabWidget.addTab(self.log_ctl, self.tr('Log'))
        tabWidget.addTab(self.aboutDlg, self.tr('About'))
        return tabWidget

    def getMenu(self):
        exit_action = QtWidgets.QAction(
            self.tr('&Exit'), self, triggered=self.quit)
        about_action = QtWidgets.QAction(
            self.tr('&About'), self, triggered=self.about)
        show_action = QtWidgets.QAction(
            self.tr('&Show Alltray'),
            self,
            triggered=partial(self.trayActivated, QtWidgets.QSystemTrayIcon.Trigger)
        )
        menu = QtWidgets.QMenu(self)
        menu.addAction(show_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        return menu

    def trayActivated(self, reason):
        if reason in (
                QtWidgets.QSystemTrayIcon.Trigger,
                QtWidgets.QSystemTrayIcon.DoubleClick):
            self.show()

    def closeEvent(self, event):
        self.saveSettings()
        if self.tray.isVisible():
            self.hide()
            event.ignore()

    def applyCommand(self, button):
        if self.buttonBox.buttonRole(button) == QtWidgets.QDialogButtonBox.RejectRole:
            self.close()
        elif self.buttonBox.buttonRole(button) == QtWidgets.QDialogButtonBox.ApplyRole:
            icon_path = self.general_ctl.icon_path.text()
            app_cmd = self.general_ctl.app_path.toPlainText()
            tooltip = self.general_ctl.tooltip.text()
            self.saveSettings()
            # XXX: crash, why?
            # icon = QtWidgets.QFileIconProvider().icon(
            #     QtCore.QFileInfo(icon_path)
            # )
            icon = QtGui.QIcon(icon_path)
            self.setWindowIcon(icon)
            self.tray.setIcon(icon)
            self.tray.setToolTip(tooltip)
            self.tray.show()
            self.runCommand(app_cmd)

    def saveSettings(self):
        icon_path = self.general_ctl.icon_path.text()
        app_cmd = self.general_ctl.app_path.toPlainText()
        tooltip = self.general_ctl.tooltip.text()
        app_run = self.general_ctl.app_run.isChecked()
        self.settings.setValue('icon_path', icon_path)
        self.settings.setValue('app_cmd', app_cmd)
        self.settings.setValue('tooltip', tooltip)
        self.settings.setValue('app_run', app_run)

    def runCommand(self, app_cmd):
        if not app_cmd:
            self.log_ctl.append('no cmd')
            return
        cmd = shlex.split(app_cmd)
        if os.path.dirname(cmd[0]):
            cmd[0] = os.path.realpath(cmd[0])
        # kill current process
        self.killCommand()
        # start new process
        self.log_ctl.append(' '.join(cmd))
        kwargs = {}
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['universal_newlines'] = True
        kwargs['shell'] = False
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            kwargs['startupinfo'] = si
        self.process = subprocess.Popen(
            cmd,
            **kwargs
        )
        self.logThread = LogThread(self.process, self)
        self.logThread.start()

    def killCommand(self):
        if self.logThread:
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except Exception as err:
                self.log_ctl.append('The command: %s' % err)
            self.logThread.kill()
            self.logThread.join()
            self.logThread = None

    def about(self):
        dlg = AboutDialog(self)
        dlg.show()

    def quit(self):
        self.tray.hide()
        self.killCommand()
        QtWidgets.qApp.quit()


class GeneralWidget(QtWidgets.QWidget):
    def __init__(self, parent, settings):
        super(GeneralWidget, self).__init__(parent)
        main_layout = QtWidgets.QVBoxLayout()
        icon_folder = QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Folder)
        # command line application don't has icon, so you may set any icon.
        iconGroup = QtWidgets.QGroupBox(self.tr('Icon'))
        hlayout = QtWidgets.QHBoxLayout()
        self.icon_ctl = QtWidgets.QLabel()
        icon = QtGui.QIcon(self.windowIcon())
        self.icon_ctl.setPixmap(icon.pixmap(32, 32))
        self.icon_ctl.setFrameStyle(QtWidgets.QFrame.StyledPanel | QtWidgets.QFrame.Plain)
        hlayout.addWidget(self.icon_ctl)
        vlayout = QtWidgets.QVBoxLayout()
        icon_label = QtWidgets.QLabel(self.tr('path:'))
        vlayout.addWidget(icon_label)
        self.icon_path = QtWidgets.QLineEdit()
        icon_browser = QtWidgets.QPushButton(icon_folder, '')
        icon_browser.setFlat(True)
        icon_browser.clicked.connect(self.iconBrowser)
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(self.icon_path)
        h_layout.addWidget(icon_browser)
        h_layout.setStretch(0, 1)
        vlayout.addLayout(h_layout)
        hlayout.addLayout(vlayout)
        iconGroup.setLayout(hlayout)

        appGroup = QtWidgets.QGroupBox(self.tr('Application'))
        vlayout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        app_label = QtWidgets.QLabel(self.tr('path:'))
        self.app_path = QtWidgets.QPlainTextEdit()
        app_browser = QtWidgets.QPushButton(icon_folder, '')
        app_browser.setFlat(True)
        app_browser.clicked.connect(self.applicationBrowser)
        hlayout.addWidget(app_label)
        hlayout.addWidget(app_browser)
        hlayout.setStretch(0, 1)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.app_path)
        vlayout.setStretch(1, 1)
        appGroup.setLayout(vlayout)

        tooltipGroup = QtWidgets.QGroupBox(self.tr('Tooltip'))
        vlayout = QtWidgets.QVBoxLayout()
        self.tooltip = QtWidgets.QLineEdit()
        vlayout.addWidget(self.tooltip)
        tooltipGroup.setLayout(vlayout)

        self.app_run = QtWidgets.QCheckBox(self.tr('Run directly, not show dialog.'))

        app_cmd = settings.value('app_cmd', '', type=str)
        icon_path = settings.value('icon_path', '', type=str)
        self.icon_path.setText(icon_path)
        self.app_path.appendPlainText(app_cmd)
        tooltip = settings.value(
            'tooltip',
            self.tr('[All Tray] I\'m here!'),
            type=str
        )
        self.tooltip.setText(tooltip)
        app_run = settings.value('app_run', False, type=bool)
        self.app_run.setChecked(app_run)

        main_layout.addWidget(iconGroup)
        main_layout.addWidget(appGroup)
        main_layout.addWidget(tooltipGroup)
        main_layout.addWidget(self.app_run)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def getFilePath(self):
        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr('Selected file'),
            '',
            "All Files (*)",
        )
        return file_path

    def iconBrowser(self):
        paths = self.getFilePath()
        self.icon_path.setText(paths[0])
        icon = QtWidgets.QFileIconProvider().icon(
            QtCore.QFileInfo(paths[0]))
        self.icon_ctl.setPixmap(icon.pixmap(32, 32))

    def applicationBrowser(self):
        paths = self.getFilePath()
        self.app_path.appendPlainText(paths[0])


class LogWidget(QtWidgets.QWidget):
    appended = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(LogWidget, self).__init__(parent)
        self.mono_font = QtGui.QFont('Monospace')
        main_layout = QtWidgets.QVBoxLayout()
        self.text_ctl = QtWidgets.QPlainTextEdit(self)
        self.text_ctl.setFont(self.mono_font)
        self.text_ctl.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.text_ctl.setReadOnly(True)
        main_layout.addWidget(self.text_ctl)
        self.setLayout(main_layout)
        self.appended.connect(self.append)

    def sizeHint(self):
        # width = QtGui.QFontMetrics(self.mono_font).width('=' * 80)
        width = 500
        return QtCore.QSize(width, -1)

    @QtCore.pyqtSlot(str)
    def append(self, line):
        self.text_ctl.moveCursor(QtGui.QTextCursor.End)
        self.text_ctl.moveCursor(QtGui.QTextCursor.StartOfLine)
        self.text_ctl.appendPlainText(line)


class AboutWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(AboutWidget, self).__init__(parent)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addStretch(1)
        icon_ctl = QtWidgets.QLabel()
        app_icon = QtWidgets.QApplication.windowIcon()
        icon_ctl.setPixmap(app_icon.pixmap(32, 32))
        hlayout.addWidget(icon_ctl)
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(QtWidgets.QLabel(
            self.tr('All Tray v%s' % __version__)
        ))
        vlayout.addWidget(QtWidgets.QLabel(self.tr('Tray all application.')))
        hlayout.addLayout(vlayout)
        hlayout.addStretch(1)
        self.setLayout(hlayout)


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(self.tr('All Tray'))
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(AboutWidget(self))
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.close)
        main_layout.addWidget(buttonBox)
        self.setLayout(main_layout)

    def closeEvent(self, event):
        self.hide()
        event.ignore()


class LogThread():
    process = None
    t1 = None

    def __init__(self, process, logWin):
        self.logWin = logWin
        self.process = process
        self.system_encoding = locale.getpreferredencoding()
        self.log('System encoding: %s' % self.system_encoding, force=True)

    def kill(self):
        pass

    def join(self):
        self.t1.join()
        self.t2.join()

    def log(self, text, force=False):
        if force or not self.logWin.isHidden():
            self.logWin.log_ctl.appended.emit(text)

    def start(self):
        """
        It will get log information if application flush its buffer.
        bug:
        sys.stdout, sys.stderr block stream sometimes
        """
        def tee_pipe(pipe, log):
            count = 0
            # for line in pipe.readline():
            for line in iter(pipe.readline, ''):
                count += 1
                log(line.rstrip('\n\r'))

        self.t1 = threading.Thread(target=tee_pipe, args=(self.process.stdout, self.log))
        self.t1.start()
        self.t2 = threading.Thread(target=tee_pipe, args=(self.process.stderr, self.log))
        self.t2.start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='default', help='command group')
    parser.add_argument('--tooltip', help='tray tool tip')
    parser.add_argument('--icon', help='command icon')
    parser.add_argument('command', nargs='?', help='To run command')
    args = parser.parse_args()

    if sys.platform == 'win32':
        if args.config == 'default':
            args.config = 'alltray.ini'
        settings = QtCore.QSettings(args.config, QtCore.QSettings.IniFormat)
    else:
        settings = QtCore.QSettings('alltray', args.config)
    if args.icon:
        settings.setValue('icon_path', args.icon)
    if args.command:
        settings.setValue('app_cmd', args.command)
    if args.tooltip:
        settings.setValue('tooltip', args.tooltip)

    # qt path
    qt_path = os.path.join(os.path.dirname(QtCore.__file__))
    QtWidgets.QApplication.addLibraryPath(qt_path)
    QtWidgets.QApplication.addLibraryPath(os.path.join(qt_path, 'plugins'))

    app = QtWidgets.QApplication(sys.argv)
    if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        QtWidgets.QMessageBox.critical(
            None,
            "Sorry",
            "I couldn't detect any system tray on this system."
        )
        sys.exit(1)
    app_icon = QtGui.QIcon('Apps-wheelchair.ico')
    app.setWindowIcon(app_icon)
    icon_path = settings.value('icon_path', '', type=str)
    if not icon_path:
        if sys.platform == 'win32':
            icon = app_icon
            # icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(sys.argv[0]))
        # elif sys.platform == 'darwin':
        #     icon = QtGui.QIcon('Apps-wheelchair.icns')
        elif sys.platform == 'linux2':
            icon = QtGui.QIcon.fromTheme('preferences-desktop-accessibility')
        else:
            icon = QtGui.QIcon('Apps-wheelchair.ico')
    else:
        # icon = QtWidgets.QFileIconProvider().icon(QtCore.QFileInfo(icon_path))
        icon = QtGui.QIcon(icon_path)
    win = TrayDialog(settings)
    win.setWindowIcon(icon)
    win.create()
    app_cmd = settings.value('app_cmd', type=str)
    app_run = settings.value('app_run', type=bool)
    if app_run:
        win.hide()
        win.runCommand(app_cmd)
    else:
        win.show()
    sys.exit(app.exec_())
