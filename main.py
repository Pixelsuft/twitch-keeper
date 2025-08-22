import sys
from PyQt6 import QtWidgets
from ui_main import Ui_MainWindow


class App:
    def __init__(self, args: list):
        self.exit_code = 0
        self.app = QtWidgets.QApplication(args)
        self.main_win = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_win)

    def run(self) -> None:
        self.main_win.show()
        self.exit_code = self.app.exec()


if __name__ == "__main__":
    tk_app = App(sys.argv)
    tk_app.run()
    sys.exit(tk_app.exit_code)
