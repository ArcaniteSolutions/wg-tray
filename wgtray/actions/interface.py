from itertools import chain
import logging
import pathlib
import random
import subprocess
import threading


from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QAction, QSystemTrayIcon


RES_PATH = pathlib.Path(__file__).parent.parent.resolve() / "res"

logger = logging.getLogger(__name__)


class WGInterface(QAction):
    done = pyqtSignal(bool, str, name="done")  # necessary to put outside of __init__

    def __init__(self, name, parent, is_up):
        super().__init__(name, parent)

        self.name = name
        self.parent = parent
        self.is_up = is_up

        self.triggered.connect(self.toggle)
        self.done.connect(self.check_status)

    def setUp(self, up):
        self.is_up = up

    def updateIcon(self):
        if self.is_up:
            icon_path = f"{RES_PATH}/green_arrow_up.png"
        else:
            icon_path = f"{RES_PATH}/grey_arrow_down.png"
        self.setIcon(QIcon(icon_path))

    def toggle(self):
        # Loading animation
        self.loadingSpinner = QMovie(f"{RES_PATH}/loader.gif")
        self.loadingSpinner.frameChanged.connect(lambda: self.setIcon(QIcon(self.loadingSpinner.currentPixmap())))
        self.loadingSpinner.start()
        # Launch command
        t = threading.Thread(target=self.bring_up_down, args=(self.is_up,))
        t.start()

    @pyqtSlot(bool, str)
    def check_status(self, is_up, err_message):
        self.is_up = is_up

        if err_message:
            self.parent.tray.showMessage("Error", err_message, QSystemTrayIcon.NoIcon)
        self.loadingSpinner.stop()
        self.updateIcon()

    def bring_up_down(self, is_up):
        kw = "down" if is_up else "up"
        subp = subprocess.Popen(f"sudo wg-quick {kw} {self.name}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        _, std_err = subp.communicate()  # blocking
        stat, err_msg = is_up, ""
        if subp.returncode == 0:
            stat = not is_up  # toggle was successful
        else:
            err_msg = std_err.decode()

        self.done.emit(stat, err_msg)


class WGInterfaceAll(QAction):
    done = pyqtSignal(int, name="done")  # necessary to put outside of __init__

    def __init__(self, name, parent, interfaces, type_, subgroups=None, pick_one_at_random=False, refresh=None):
        super().__init__(name, parent)

        self.name = name
        self.parent = parent
        self.interfaces = interfaces
        self.type_ = type_
        self.refresh = refresh

        self.subgroups = subgroups if subgroups else []
        self.pick_one_at_random = pick_one_at_random

        self.triggered.connect(self.toggle)
        self.done.connect(self._done)
        self.updateIcon()

    def updateIcon(self):
        if self.type_:
            icon_path = f"{RES_PATH}/green_arrow_up.png"
        else:
            icon_path = f"{RES_PATH}/grey_arrow_down.png"
        self.setIcon(QIcon(icon_path))

    @pyqtSlot(int)
    def _done(self, count):

        pt = "upped" if self.type_ else "downed"
        if count:
            self.parent.tray.showMessage("Informations", f"Successfully {pt} {count} interface(s)", QSystemTrayIcon.NoIcon)

        else:
            self.parent.tray.showMessage("Warning", f"No interfaces where {pt}", QSystemTrayIcon.NoIcon)

        self.loadingSpinner.stop()
        self.updateIcon()

        if self.refresh:
            self.refresh()

    def toggle(self):
        # Loading animation
        self.loadingSpinner = QMovie(f"{RES_PATH}/loader.gif")
        self.loadingSpinner.frameChanged.connect(lambda: self.setIcon(QIcon(self.loadingSpinner.currentPixmap())))
        self.loadingSpinner.start()

        # Launch command
        t = threading.Thread(target=self._toggle)
        t.start()

    def get_iterfaces_to_workon(self):
        """Return the list of interfaces to down/up."""

        if self.subgroups:
            return chain.from_iterable(group.get_iterfaces_to_workon() for group in self.subgroups)

        if self.pick_one_at_random:
            return random.choices(self.interfaces, k=1)

        return self.interfaces

    def _toggle(self):
        kw = "up" if self.type_ else "down"

        def _interface_open(interface):
            subp = subprocess.Popen(f"sudo wg-quick {kw} {interface}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            _, std_err = subp.communicate()  # blocking
            if subp.returncode == 0:
                return True, ""

            return False, std_err.decode()

        upped_interface = 0

        for interface in self.get_iterfaces_to_workon():
            success, err_msg = _interface_open(interface)

            if success:
                logger.info(f"Interface: {interface}, sucessfully mounted")
                upped_interface += 1

            else:
                logger.info(f"Interface: {interface}, error while mounting: {err_msg}")

        self.done.emit(upped_interface)
