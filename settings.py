import json
from PyQt6 import QtWidgets, QtGui
from ui_sets import Ui_SettingsWindow


class Settings:
    def __init__(self, app) -> None:
        self.app = app
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_SettingsWindow()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.ui, self.app.dark)
        self.ui.clientEdit.setText(app.client_id)
        self.ui.oauthEdit.setText(app.oauth_token)
        self.ui.saveButton.clicked.connect(self.save)
        self.ui.cancelButton.clicked.connect(self.cancel)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.applyButton.clicked.connect(self.apply)
        self.win.show()

    def apply(self) -> None:
        self.app.client_id = self.ui.clientEdit.text()
        self.app.oauth_token = self.ui.oauthEdit.text()

    def reset(self) -> None:
        self.ui.clientEdit.setText('kimne78kx3ncx6brgo4mv6wki5h1ko')
        self.ui.oauthEdit.setText('')

    def save(self) -> None:
        self.apply()
        open(self.app.conf_path, 'w', encoding='utf-8').write(json.dumps({
            'client_id': self.app.client_id,
            'oauth_token': self.app.oauth_token
        }))
        self.win.close()

    def cancel(self) -> None:
        self.win.close()

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        ev.accept()
        self.app.forms.remove(self)
        self.app = None
