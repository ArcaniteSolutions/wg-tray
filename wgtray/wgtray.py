import argparse
import os
import pathlib
import signal
import sys


from PyQt5.QtCore import pyqtSlot, QCoreApplication, QTimer
from PyQt5.QtGui import QContextMenuEvent, QIcon, QMovie
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon


from . import __description__, __version__
from .actions.interface import WGInterface


RES_PATH = pathlib.Path(__file__).parent.resolve() / "res"


class WGTrayIcon(QSystemTrayIcon):
    def __init__(self, config_path=None):
        super().__init__()

        self.menu = WGMenu(self, config_path)
        self.setContextMenu(self.menu)
        self.activated.connect(self.activateMenu)  # show also on left click

        self.setIcon(QIcon(f"{RES_PATH}/icon.png"))

        self.show()

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def activateMenu(self, activationReason):
        if activationReason == QSystemTrayIcon.Trigger:
            self.menu.showTearOff()


class WGMenu(QMenu):
    def __init__(self, tray, config_path):
        super().__init__()

        self.tray = tray

        if config_path:
            with open(config_path) as f:
                itfs = f.read()
        else:
            itfs = os.popen("sudo ls /etc/wireguard | grep .conf | awk -F \".\" '{print $1}'").read()
        itfs_up = self.read_status()

        for itf_name in itfs.strip().split():
            action = WGInterface(itf_name, self, itf_name in itfs_up)
            action.updateIcon()
            self.addAction(action)

        self.addSeparator()

        # Options for the tear off menu

        # Refresh data
        self.refresh = QAction("Refresh", self, triggered=self.startRefresh)
        self.addAction(self.refresh)
        self.refresh.setVisible(False)

        self.refreshTimer = QTimer()
        self.refreshTimer.timeout.connect(self.stopRefresh)

        # Close menu
        self.closeTearOff = QAction("Close menu", self, triggered=self.closeMenu)
        self.addAction(self.closeTearOff)
        self.closeTearOff.setVisible(False)

        self.addAction(QAction("Quit", self, triggered=self.quit))

        self.aboutToShow.connect(self.preshowMenu)

    def read_status(self):
        return os.popen("sudo wg | grep interface | awk '{print $2}'").read().strip().split()

    def reloadStatus(self):
        itfs_up = self.read_status()
        for action in self.actions():
            if isinstance(action, WGInterface):
                action.setUp(action.text() in itfs_up)
                action.updateIcon()

    def showTearOff(self):
        self.showTearOffMenu(QApplication.desktop().availableGeometry().center())
        self.closeTearOff.setVisible(True)
        self.refresh.setVisible(True)

        # Find window popup
        tornPopup = None
        for tl in QApplication.topLevelWidgets():
            if tl.metaObject().className() == "QTornOffMenu":
                tornPopup = tl
                break

        if tornPopup:
            # Center window
            screen = QApplication.desktop().availableGeometry()
            qtRectangle = tornPopup.frameGeometry()
            qtRectangle.moveCenter(screen.center())
            tornPopup.move(qtRectangle.topLeft())

    @pyqtSlot()
    def preshowMenu(self):
        if not self.isTearOffMenuVisible():
            self.closeTearOff.setVisible(False)
            self.refresh.setVisible(False)
            self.updateGeometry()

        self.reloadStatus()

    @pyqtSlot()
    def startRefresh(self):
        # Launch timer for 0.5 seconds
        self.refreshTimer.start(500)
        # Loading animation
        self.refreshSpinner = QMovie(f"{RES_PATH}/loader.gif")
        self.refreshSpinner.frameChanged.connect(lambda: self.refresh.setIcon(QIcon(self.refreshSpinner.currentPixmap())))
        self.refreshSpinner.start()
        # Actual refresh
        self.reloadStatus()

    @pyqtSlot()
    def stopRefresh(self):
        self.refreshSpinner.stop()
        self.refresh.setIcon(QIcon())
        self.refreshTimer.stop()

    @pyqtSlot()
    def closeMenu(self):
        self.closeTearOff.setVisible(False)
        self.refresh.setVisible(False)
        self.hideTearOffMenu()

    @pyqtSlot()
    def quit(self):
        QCoreApplication.quit()


def parse_args():

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument("-v", "--version", help="show program version info and exit", action="version", version=__version__)
    parser.add_argument(
        "-c",
        "--config",
        help="path to the config file listing all WireGuard interfaces (if none is provided, use root privileges to look up in /etc/wireguard/)",
        default=None,
        type=str,
    )

    args = parser.parse_args()

    return args.config


app = QApplication(sys.argv)

config_path = parse_args()

WGTrayIcon(config_path)

signal.signal(signal.SIGINT, signal.SIG_DFL)

sys.exit(app.exec_())
