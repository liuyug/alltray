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

from PyQt4 import QtGui, QtCore

from alltray import __version__


class TrayDialog(QtGui.QDialog):
    logThread = None

    def __init__(self, settings, parent=None):
        super(TrayDialog, self).__init__(parent)
        self.settings = settings
        icon_path = settings.value('icon_path').toString()
        if icon_path.isEmpty():
            if sys.platform == 'win32':
                icon = QtGui.QIcon(QtGui.QFileIconProvider().icon(QtCore.QFileInfo(sys.argv[0])))
            else:
                icon = QtGui.QIcon.fromTheme('preferences-desktop-accessibility')
        else:
            icon = QtGui.QIcon(QtGui.QFileIconProvider().icon(QtCore.QFileInfo(icon_path)))
        self.setWindowIcon(icon)
        self.setWindowTitle(self.tr('All Tray'))
        self.setLayout(self.getLayout())
        self.tray = QtGui.QSystemTrayIcon(self)
        self.tray.setContextMenu(self.getMenu())
        self.tray.setIcon(icon)
        tooltip = settings.value('tooltip').toString()
        if tooltip.isEmpty():
            tooltip = self.tr('[All Tray] I\'m here!')
        self.tray.setToolTip(tooltip)
        self.tray.activated.connect(self.trayActivated)

        app_cmd = settings.value('app_cmd').toString()
        self.general_ctl.icon_path.setText(icon_path)
        self.general_ctl.app_path.appendPlainText(app_cmd)
        self.general_ctl.tooltip.setText(tooltip)

        app_run = settings.value('app_run').toBool()
        self.general_ctl.app_run.setChecked(app_run)

        if app_run:
            self.tray.show()

    def getLayout(self):
        main_layout = QtGui.QVBoxLayout()
        tabWidget = QtGui.QTabWidget(self)
        self.general_ctl = GeneralWidget(self.settings, tabWidget)
        self.log_ctl = LogWidget(tabWidget)
        dlg = QtGui.QDialog(self)
        about = AboutWidget(dlg)
        about_layout = QtGui.QVBoxLayout()
        about_layout.addWidget(about)
        about_layout.addStretch(1)
        dlg.setLayout(about_layout)
        tabWidget.addTab(self.general_ctl, self.tr('General'))
        tabWidget.addTab(self.log_ctl, self.tr('Log'))
        tabWidget.addTab(dlg, self.tr('About'))
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.applyCommand)
        main_layout.addWidget(tabWidget)
        main_layout.addWidget(self.buttonBox)
        return main_layout

    def getMenu(self):
        exit_action = QtGui.QAction(
            self.tr('&Exit'), self, triggered=self.quit)
        about_action = QtGui.QAction(
            self.tr('&About'), self, triggered=self.about)
        show_action = QtGui.QAction(
            self.tr('&Show Alltray'),
            self,
            triggered=partial(self.trayActivated, QtGui.QSystemTrayIcon.Trigger)
        )
        menu = QtGui.QMenu(self)
        menu.addAction(show_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        return menu

    def trayActivated(self, reason):
        if reason in (
                QtGui.QSystemTrayIcon.Trigger,
                QtGui.QSystemTrayIcon.DoubleClick):
            self.show()

    def closeEvent(self, event):
        self.saveSettings()
        if self.tray.isVisible():
            self.hide()
            event.ignore()

    def applyCommand(self, button):
        if self.buttonBox.buttonRole(button) == QtGui.QDialogButtonBox.RejectRole:
            self.close()
        elif self.buttonBox.buttonRole(button) == QtGui.QDialogButtonBox.ApplyRole:
            icon_path = self.general_ctl.icon_path.text()
            app_cmd = self.general_ctl.app_path.toPlainText()
            tooltip = self.general_ctl.tooltip.text()
            self.saveSettings()
            icon = QtGui.QFileIconProvider().icon(
                QtCore.QFileInfo(icon_path))
            self.setWindowIcon(icon)
            self.tray.setToolTip(tooltip)
            self.tray.show()
            self.hide()
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
        cmd = shlex.split(unicode(app_cmd.toUtf8(), encoding='utf8'))
        if os.path.dirname(cmd[0]):
            cmd[0] = os.path.realpath(cmd[0])
        if self.logThread:
            self.process.kill()
            self.logThread.kill()
            self.logThread.join()
        self.log_ctl.append(' '.join(cmd))
        kwargs = {}
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = subprocess.PIPE
        kwargs['shell'] = False
        if sys.platform == 'win32':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.dwFlags |= subprocess.STARTF_USESTDHANDLES
            kwargs['startupinfo'] = si
        self.process = subprocess.Popen(
            cmd,
            **kwargs
        )
        self.logThread = LogThread(self.process, self)
        self.logThread.start()

    def killCommand(self):
        if self.logThread:
            self.process.kill()
            self.logThread.kill()
            self.logThread.join()
            self.logThread = None

    def about(self):
        dlg = AboutDialog(self)
        dlg.show()

    def quit(self):
        self.tray.hide()
        self.killCommand()
        QtGui.qApp.quit()


class GeneralWidget(QtGui.QWidget):
    def __init__(self, settings, parent=None):
        super(GeneralWidget, self).__init__(parent)
        main_layout = QtGui.QVBoxLayout()
        icon_folder = QtGui.QFileIconProvider().icon(QtGui.QFileIconProvider.Folder)
        # command line application don't has icon, so you may set any icon.
        iconGroup = QtGui.QGroupBox(self.tr('Icon'))
        hlayout = QtGui.QHBoxLayout()
        self.icon_ctl = QtGui.QLabel()
        self.icon_ctl.setPixmap(self.windowIcon().pixmap(32, 32))
        self.icon_ctl.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        hlayout.addWidget(self.icon_ctl)
        vlayout = QtGui.QVBoxLayout()
        icon_label = QtGui.QLabel(self.tr('path:'))
        vlayout.addWidget(icon_label)
        self.icon_path = QtGui.QLineEdit()
        icon_browser = QtGui.QPushButton(icon_folder, '')
        icon_browser.setFlat(True)
        icon_browser.clicked.connect(self.iconBrowser)
        h_layout = QtGui.QHBoxLayout()
        h_layout.addWidget(self.icon_path)
        h_layout.addWidget(icon_browser)
        h_layout.setStretch(0, 1)
        vlayout.addLayout(h_layout)
        hlayout.addLayout(vlayout)
        iconGroup.setLayout(hlayout)

        appGroup = QtGui.QGroupBox(self.tr('Application'))
        vlayout = QtGui.QVBoxLayout()
        hlayout = QtGui.QHBoxLayout()
        app_label = QtGui.QLabel(self.tr('path:'))
        self.app_path = QtGui.QPlainTextEdit()
        app_browser = QtGui.QPushButton(icon_folder, '')
        app_browser.setFlat(True)
        app_browser.clicked.connect(self.applicationBrowser)
        hlayout.addWidget(app_label)
        hlayout.addWidget(app_browser)
        hlayout.setStretch(0, 1)
        vlayout.addLayout(hlayout)
        vlayout.addWidget(self.app_path)
        vlayout.setStretch(1, 1)
        appGroup.setLayout(vlayout)

        tooltipGroup = QtGui.QGroupBox(self.tr('Tooltip'))
        vlayout = QtGui.QVBoxLayout()
        self.tooltip = QtGui.QLineEdit()
        vlayout.addWidget(self.tooltip)
        tooltipGroup.setLayout(vlayout)

        self.app_run = QtGui.QCheckBox(self.tr('Run directly, not show dialog.'))
        self.app_run.setChecked(False)

        main_layout.addWidget(iconGroup)
        main_layout.addWidget(appGroup)
        main_layout.addWidget(tooltipGroup)
        main_layout.addWidget(self.app_run)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def getFilePath(self):
        file_path = QtGui.QFileDialog.getOpenFileName(
            self,
            self.tr('Selected file'),
            '',
            "All Files (*)",
        )
        return file_path

    def iconBrowser(self):
        path = self.getFilePath()
        self.icon_path.setText(path)
        icon = QtGui.QFileIconProvider().icon(
            QtCore.QFileInfo(path))
        self.icon_ctl.setPixmap(icon.pixmap(32, 32))

    def applicationBrowser(self):
        path = self.getFilePath()
        self.app_path.appendPlainText(path)


class LogWidget(QtGui.QWidget):
    appended = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(LogWidget, self).__init__(parent)
        self.mono_font = QtGui.QFont('Monospace')
        main_layout = QtGui.QVBoxLayout()
        self.text_ctl = QtGui.QPlainTextEdit(self)
        self.text_ctl.setFont(self.mono_font)
        self.text_ctl.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)
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


class AboutWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(AboutWidget, self).__init__(parent)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addStretch(1)
        icon_ctl = QtGui.QLabel()
        icon_ctl.setPixmap(self.windowIcon().pixmap(32, 32))
        hlayout.addWidget(icon_ctl)
        vlayout = QtGui.QVBoxLayout()
        vlayout.addWidget(QtGui.QLabel(
            self.tr('All Tray v%s' % __version__)
        ))
        vlayout.addWidget(QtGui.QLabel(self.tr('Tray all application.')))
        hlayout.addLayout(vlayout)
        hlayout.addStretch(1)
        self.setLayout(hlayout)


class AboutDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(self.tr('All Tray'))
        main_layout = QtGui.QVBoxLayout()
        main_layout.addWidget(AboutWidget(self))
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
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
            for line in iter(pipe.readline, ''):
                line = unicode(line, self.system_encoding)
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

    app = QtGui.QApplication(sys.argv)
    if not QtGui.QSystemTrayIcon.isSystemTrayAvailable():
        QtGui.QMessageBox.critical(
            None,
            "Sorry",
            "I couldn't detect any system tray on this system."
        )
        sys.exit(1)
    win = TrayDialog(settings)
    app_cmd = settings.value('app_cmd').toString()
    app_run = settings.value('app_run').toBool()
    if app_run:
        win.hide()
        win.runCommand(app_cmd)
    else:
        win.show()
    sys.exit(app.exec_())
