try:
    import grequests  # noqa
    has_grequests = True
except ImportError:
    has_grequests = False
import requests
from PyQt6 import QtWidgets, QtGui
from ui_stream import Ui_StreamDownloaderWindow


class StreamDown:
    def __init__(self, app) -> None:
        self.app = app
        self.locks = 0
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_StreamDownloaderWindow()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.ui, self.app.dark)
        self.ui.logList.setAutoScroll(True)
        self.ui.downButton.clicked.connect(self.download)
        self.ui.stopButton.clicked.connect(self.stop)
        self.ui.outButton.clicked.connect(self.select_out)
        self.ui.ffmpegEdit.setText('ffmpeg -i pipe:0 %out%')
        self.win.show()

    def stop(self) -> None:
        self.ui.stopButton.setEnabled(False)

    def download(self) -> None:
        pass

    def set_info_enabled(self, enabled: bool):
        pass

    def log_clear(self) -> None:
        self.ui.logList.clear()

    def log_msg(self, data: str) -> None:
        self.ui.logList.addItem(data)
        self.ui.logList.scrollToBottom()

    def select_out(self) -> None:
        ret = QtWidgets.QFileDialog.getSaveFileName(self.win, 'Select output video path', None)
        self.ui.outEdit.setText(ret[0] or '')

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        if self.locks > 0:
            ev.ignore()
            self.log_msg('Can\'t close window because there are operations pending')
            return
        ev.accept()
        self.app.forms.remove(self)
        self.app = None
