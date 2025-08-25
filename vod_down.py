from PyQt6 import QtWidgets, QtGui
from ui_vod import Ui_VodDownloader


class VodDown:
    def __init__(self, app):
        self.app = app
        self.locks = 0
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_VodDownloader()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.app.dark)
        self.ui.fetchButton.clicked.connect(self.fetch_info)
        # TODO: remove
        self.ui.urlEdit.setText('https://www.twitch.tv/videos/2548554034')
        self.win.show()

    def fetch_info(self) -> None:
        url = self.ui.urlEdit.text().strip()
        print(url)

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        if self.locks > 0:
            ev.ignore()
            return
        ev.accept()
        # TODO: remove
        if 1:
            return
        self.app.forms.remove(self)
        self.app = None
