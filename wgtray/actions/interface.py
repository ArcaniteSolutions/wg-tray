import pathlib
import subprocess
import threading


from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QMovie
from PyQt5.QtWidgets import QAction, QSystemTrayIcon


RES_PATH = pathlib.Path(__file__).parent.parent.resolve() / "res"


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
