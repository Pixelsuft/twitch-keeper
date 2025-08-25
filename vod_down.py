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
        self.ui.logList.setAutoScroll(True)
        self.ui.fetchButton.clicked.connect(self.fetch_info)
        # TODO: remove
        self.ui.urlEdit.setText('https://www.twitch.tv/videos/2548554034')
        self.win.show()

    def fetch_info(self) -> None:
        self.log_clear()
        try:
            url = self.ui.urlEdit.text().strip()
            if 'twitch.tv/videos/' not in url:
                raise RuntimeError('Incorrect twitch link')
            vid_id = int(url.strip('/').split('/')[-1])
        except Exception as err:
            self.log_msg(f'Failed to get video ID: {err}')
            return
        self.win.setWindowTitle('VOD Downloader')
        self.ui.startTime.setTime(QtCore.QTime(0, 0, 0))
        self.ui.endTime.setTime(QtCore.QTime(0, 0, 0))
        self.fetcher.headers = self.app.get_default_headers()
        self.fetcher.vid = vid_id
        self.locks += 1
        self.set_info_enabled(False)
        self.fetcher.start()

    def on_fetch_info_progress(self, code: int, status: str, text: str) -> None:
        if code == 0:
            self.locks -= 1
            self.set_info_enabled(True)
            if int(status) != 200:
                self.log_msg(f'Twitch API request failed with status {status}: {text}')
                return
            try:
                data = json.loads(text)['data']
                title = str(data['video']['title'])
                length = int(data['video']['lengthSeconds'])
                self.log_msg(f'Video title: {title}')
                self.log_msg(f'Video length: {length}s')
                self.log_msg(f'Video status: {data["video"]["status"]}')
            except Exception as err:
                self.log_msg(f'Failed to parse video info: {err}')
                return
            self.win.setWindowTitle(title + ' [VOD Downloader]')
            self.ui.endTime.setTime(QtCore.QTime.fromMSecsSinceStartOfDay(length * 1000))

    def set_info_enabled(self, enabled: bool):
        self.ui.urlEdit.setEnabled(enabled)
        self.ui.fetchButton.setEnabled(enabled)
        self.ui.startTime.setEnabled(enabled)
        self.ui.endTime.setEnabled(enabled)
        self.ui.chunkEdit.setEnabled(enabled)
        self.ui.downButton.setEnabled(enabled)

    def log_clear(self) -> None:
        self.ui.logList.clear()

    def log_msg(self, data: str) -> None:
        self.ui.logList.addItem(data)
        self.ui.logList.scrollToBottom()

    def close_event(self, ev: QtGui.QCloseEvent) -> None:
        if self.locks > 0:
            ev.ignore()
            self.log_msg('Can\'t close window because there are operations pending')
            return
        ev.accept()
        # TODO: remove
        if 1:
            return
        self.app.forms.remove(self)
        self.app = None
