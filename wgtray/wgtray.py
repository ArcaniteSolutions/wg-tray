from configparser import ConfigParser
import argparse
import logging
import os
import pathlib
import signal
import sys


from PyQt5.QtCore import pyqtSlot, QCoreApplication, QTimer
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon


from . import __description__, __version__
from .actions.interface import WGInterface, WGInterfaceAll


RES_PATH = pathlib.Path(__file__).parent.resolve() / "res"


class WGTrayIcon(QSystemTrayIcon):
    def __init__(self, config_path=None, config_menu=None):
        super().__init__()

        self.menu = WGMenu(self, config_path, config_menu)
        self.setContextMenu(self.menu)
        self.activated.connect(self.activateMenu)  # show also on left click

        self.setIcon(QIcon(f"{RES_PATH}/icon.png"))

        self.show()

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def activateMenu(self, activationReason):
        if activationReason == QSystemTrayIcon.Trigger:
            self.menu.showTearOff()


class WGMenu(QMenu):
    def __init__(self, tray, config_path, config_menu=None):
        super().__init__()

        self.tray = tray
        self.config_menu = config_menu

        itfs_up = self.read_status()

        interfaces_done = []
        interface_actions = []
        self.menus = []

        if self.config_menu:
            general_pick_one_at_random = False
            if "settings" in config:
                settings = self.config_menu["settings"]
                general_pick_one_at_random = settings.get("pick_one_at_random", "false") == "true"

            for section in self.config_menu.sections():
                if section == "settings":
                    continue

                if "pick_one_at_random" in self.config_menu[section]:
                    pick_one_at_random = self.config_menu[section].get("pick_one_at_random", "false") == "true"

                else:
                    pick_one_at_random = general_pick_one_at_random

                menu = self.addMenu(str(section))
                self.menus.append(menu)

                if not menu:
                    continue

                section_interfaces = []
                for interface in self.config_menu[section]["interfaces"].strip().split():
                    action = WGInterface(interface, self, interface in itfs_up)
                    action.updateIcon()
                    menu.addAction(action)

                    section_interfaces.append(interface)

                interfaces_done.extend(section_interfaces)

                menu.addSeparator()
                interface_action = WGInterfaceAll(
                    "Up one random interface" if pick_one_at_random else "Up all interfaces",
                    self,
                    section_interfaces,
                    True,
                    pick_one_at_random=pick_one_at_random,
                    refresh=self.startRefresh,
                )
                menu.addAction(interface_action)
                interface_actions.append(interface_action)

                menu.addAction(
                    WGInterfaceAll(
                        "Down all interfaces",
                        self,
                        section_interfaces,
                        False,
                        # We want to down all interfaces, regarding of the settings for the up
                        pick_one_at_random=False,
                        refresh=self.startRefresh,
                    )
                )

        if config_path:
            with open(config_path) as f:
                itfs = f.read()
        else:
            itfs = os.popen("sudo ls /etc/wireguard | grep .conf | awk -F \".\" '{print $1}'").read()

        itfs = itfs.strip().split()

        for itf_name in itfs:
            if itf_name not in interfaces_done:
                action = WGInterface(itf_name, self, itf_name in itfs_up)
                action.updateIcon()
                self.addAction(action)

                interfaces_done.append(itf_name)

        self.addSeparator()

        self.addAction(
            WGInterfaceAll(
                "Up interfaces on all groups",
                self,
                [],
                True,
                subgroups=interface_actions,
                pick_one_at_random=False,
                refresh=self.startRefresh,
            )
        )
        self.addAction(
            WGInterfaceAll(
                "Up all interfaces",
                self,
                interfaces_done,
                True,
                pick_one_at_random=False,
                refresh=self.startRefresh,
            )
        )
        self.addAction(
            WGInterfaceAll(
                "Down interfaces on all groups",
                self,
                interfaces_done,
                False,
                pick_one_at_random=False,
                refresh=self.startRefresh,
            )
        )

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

        for menu in self.menus:
            for action in menu.actions():
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

    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-v", "--version", help="show program version info and exit", action="version", version=__version__)
    parser.add_argument(
        "-c",
        "--config",
        help="path to the config file listing all WireGuard interfaces (if none is provided, use root privileges to look up in /etc/wireguard/)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "-g",
        "--config-groups",
        help="Path to the config (.ini file) to have groups of wireguard configs.",
        default="~/.wireguard/wg_tray_groups.ini",
        type=str,
    )

    args = parser.parse_args()

    return args


logging.basicConfig(level=logging.INFO)
config = ConfigParser()

app = QApplication(sys.argv)

parser_args = parse_args()
config.read(pathlib.Path(parser_args.config_groups).expanduser())

WGTrayIcon(parser_args.config, config_menu=config)


signal.signal(signal.SIGINT, signal.SIG_DFL)

sys.exit(app.exec_())
