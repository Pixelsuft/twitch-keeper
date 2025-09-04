import os
import sys
if 1 and os.getenv('PYCHARM_HOSTED') and int(os.environ['PYCHARM_HOSTED']):
    import subprocess
    for i in ('main', 'vod', 'sets'):
        if not os.path.isfile(f'ui_{i}.py') or os.path.getmtime(f'ui_{i}.py') < os.path.getmtime(f'ui/{i}.ui'):
            print(f'Rebuilding ui_{i}.py')
            subprocess.call(['pyuic6', '-o', f'ui_{i}.py', f'ui/{i}.ui'])
from PyQt6 import QtWidgets, QtGui
from theming import Theming
from styling import Styling
from ui_main import Ui_MainWindow
from vod_down import VodDown
from settings import Settings


class App:
    def __init__(self, args: list):
        self.exit_code = 0
        self.app = QtWidgets.QApplication(args)
        self.cwd = os.path.dirname(__file__) or os.getcwd()
        # TODO: use config.json file
        self.client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
        self.oauth_token = ''
        self.forms = []
        self.theming = Theming()
        self.styling = Styling()
        self.main_win = QtWidgets.QMainWindow()
        self.main_win.closeEvent = self.close_event
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_win)
        self.main_win.setFixedSize(self.main_win.size())
        self.dark = self.theming.is_dark()
        self.theming.init_on_window(self.main_win, self.dark)
        self.styling.read_styles(os.path.join(self.cwd, 'styles'), not self.dark, self.dark)
        self.styling.apply_on_win(self.main_win, self.ui, self.dark)
        self.ui.vodButton.clicked.connect(self.spawn_vod)
        self.ui.settingsButton.clicked.connect(self.spawn_sets)

    def spawn_vod(self) -> None:
        v = VodDown(self)
        self.forms.append(v)

    def spawn_sets(self) -> None:
        if any(type(x) == Settings for x in self.forms):
            return
        s = Settings(self)
        self.forms.append(s)

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        if self.forms:
            ev.ignore()
            return
        ev.accept()

    def get_default_headers(self) -> dict:
        ret = {
            'Client-ID': self.client_id
        }
        if self.oauth_token:
            ret['Authorization'] = 'OAuth ' + self.oauth_token
        return ret

    def run(self) -> None:
        # TODO: remove
        if 0:
            self.spawn_sets()
            self.exit_code = self.app.exec()
            return
        self.main_win.show()
        self.exit_code = self.app.exec()


if __name__ == "__main__":
    tk_app = App(sys.argv)
    tk_app.run()
    sys.exit(tk_app.exit_code)
