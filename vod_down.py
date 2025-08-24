from PyQt6 import QtWidgets, QtGui
from ui_vod import Ui_VodDownloader


class VodDown:
    def __init__(self, app):
        self.app = app
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_VodDownloader()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.app.dark)
        self.win.show()

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        ev.accept()
        self.app.forms.remove(self)
        self.app = None
