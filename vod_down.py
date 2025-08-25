import json
import requests
from PyQt6 import QtWidgets, QtGui, QtCore
from ui_vod import Ui_VodDownloader


class InfoFetcher(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, str, str)

    def __init__(self) -> None:
        super().__init__()
        self.headers = {}
        self.vid = 0

    def run(self) -> None:
        data = '{"query":"query{video(id:\\"' + str(self.vid) + '\\"){title,lengthSeconds,status}}","variables":{}}'
        try:
            resp = requests.post('https://gql.twitch.tv/gql', headers=self.headers, data=data)
            self.progress.emit(0, str(resp.status_code), resp.content.decode('utf-8', errors='replace'))
        except Exception as err:
            self.progress.emit(0, '0', str(err))


class VodDown:
    def __init__(self, app):
        self.app = app
        self.locks = 0
        self.fetcher = InfoFetcher()
        self.fetcher.progress.connect(self.on_fetch_info_progress)
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_VodDownloader()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.ui, self.app.dark)
        self.ui.fetchButton.clicked.connect(self.fetch_info)
        # TODO: remove
        self.ui.urlEdit.setText('https://www.twitch.tv/videos/2548554034')
        self.win.show()

    def fetch_info(self) -> None:
        url = self.ui.urlEdit.text().strip()
        # TODO: vefiry id
        vid_id = int(url.strip('/').split('/')[-1])
        self.win.setWindowTitle('VOD Downloader')
        self.ui.startTime.setTime(QtCore.QTime(0, 0, 0))
        self.ui.endTime.setTime(QtCore.QTime(0, 0, 0))
        self.fetcher.headers = self.app.get_default_headers()
        self.fetcher.vid = vid_id
        self.locks += 1
        self.set_info_enabled(False)
        self.fetcher.start()

    def on_fetch_info_progress(self, code: int, status: str, text: str) -> None:
        print(f'TODO got message {code} {status}: {text}')
        if code == 0:
            self.locks -= 1
            self.set_info_enabled(True)
            if int(status) != 200:
                return
            try:
                data = json.loads(text)
                title = str(data['data']['video']['title'])
                length = int(data['data']['video']['lengthSeconds'])
            except Exception as err:
                print('TODO err: ' + str(err))
                return
            self.win.setWindowTitle(title + ' [VOD Downloader]')
            self.ui.endTime.setTime(QtCore.QTime(length // 3600, (length // 60) % 60, length % 60))

    def set_info_enabled(self, enabled: bool):
        self.ui.urlEdit.setEnabled(enabled)
        self.ui.fetchButton.setEnabled(enabled)
        self.ui.startTime.setEnabled(enabled)
        self.ui.endTime.setEnabled(enabled)

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
