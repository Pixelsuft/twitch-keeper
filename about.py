from PyQt6 import QtWidgets, QtGui
from ui_about import Ui_AboutWindow


class About:
    def __init__(self, app) -> None:
        self.app = app
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_AboutWindow()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.ui, self.app.dark)
        self.ui.closeButton.clicked.connect(self.win.close)
        self.win.show()

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        ev.accept()
        self.app.forms.remove(self)
        self.app = None
