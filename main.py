import os
import sys
if 1 and os.getenv('PYCHARM_HOSTED') and int(os.environ['PYCHARM_HOSTED']):
    import subprocess
    for i in ('main', ):
        if not os.path.isfile(f'ui_{i}.py') or os.path.getmtime(f'ui_{i}.py') < os.path.getmtime(f'ui/{i}.ui'):
            print(f'Rebuilding ui_{i}.py')
            subprocess.call(['pyuic6', '-o', f'ui_{i}.py', f'ui/{i}.ui'])
from PyQt6 import QtWidgets
from theming import Theming
from styling import Styling
from ui_main import Ui_MainWindow


class App:
    def __init__(self, args: list):
        self.exit_code = 0
        self.app = QtWidgets.QApplication(args)
        self.cwd = os.path.dirname(__file__) or os.getcwd()
        self.theming = Theming()
        self.styling = Styling()
        self.main_win = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_win)
        self.main_win.setFixedSize(self.main_win.size())
        self.theming.init_on_window(self.main_win)
        self.dark = self.theming.is_dark()
        self.styling.read_styles(os.path.join(self.cwd, 'styles'), not self.dark, self.dark)
        self.styling.apply_on_win(self.main_win, self.dark)

    def run(self) -> None:
        self.main_win.show()
        self.exit_code = self.app.exec()


if __name__ == "__main__":
    tk_app = App(sys.argv)
    tk_app.run()
    sys.exit(tk_app.exit_code)
