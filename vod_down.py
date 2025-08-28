import json
import math
import requests
from PyQt6 import QtWidgets, QtGui, QtCore
from ui_vod import Ui_VodDownloader
from writer import SimpleWriter


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

class SingleDownloader(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, str)
    
    def __init__(self, headers: dict, writer, chunk_url: str, mp4: bool, start_c: int, end_c: int) -> None:
        super().__init__()
        self.headers = headers
        self.writer = writer
        self.chunk_url = chunk_url
        self.mp4 = mp4
        self.ext = 'mp4' if self.mp4 else 'ts'
        self.should_stop = False
        self.start_chunk = start_c
        self.end_chunk = end_c

    def run(self) -> None:
        if self.mp4:
            try:
                data = requests.get(self.chunk_url + 'init-0.mp4', headers=self.headers)
            except Exception as err:
                self.progress.emit(0, f'Failed make request for init video ({err})')
                return
            if not data.status_code == 200 and not data.status_code == 403:
                self.progress.emit(0, f'Request failed with status code {data.status_code}')
            if data.status_code == 200:
                self.writer.write(data.content)
            else:
                self.progress.emit(1, 'Failed to obtain .mp4 data, falling back to .ts format')
                self.mp4 = False
                self.ext = 'ts'
        cur = self.start_chunk
        muted = ''
        err_count = 0
        while cur < self.end_chunk:
            if self.should_stop:
                self.progress.emit(0, 'Aborted by used')
                return
            if err_count >= 10:
                self.progress.emit(0, 'Too many errors in a row')
                return
            try:
                data = requests.get(self.chunk_url + f'{cur}{muted}.{self.ext}', headers=self.headers)
                if data.status_code == 403:
                    err_count += 1
                    # Trying to autodetect muted segments
                    self.progress.emit(1, f'Failed to download chunk {cur}{muted}.{self.ext}, trying to change muted/unmuted')
                    muted = '' if muted else '-muted'
                    continue
                if not data.status_code == 200:
                    raise RuntimeError(f'Request failed with status code {data.status_code}')
                self.writer.write(data.content)
            except Exception as err:
                err_count += 1
                self.progress.emit(1, f'Failed to download chunk {cur}{muted}.{self.ext}: {err}')
                continue
            err_count = 0
            cur += 1
            self.progress.emit(2, str(cur - self.start_chunk))
        self.progress.emit(0, 'Done')


class VodDown:
    def __init__(self, app):
        self.app = app
        self.locks = 0
        self.fetcher = InfoFetcher()
        self.fetcher.progress.connect(self.on_fetch_info_progress)
        self.downloader = None
        self.win = QtWidgets.QMainWindow()
        self.win.closeEvent = self.close_event
        self.ui = Ui_VodDownloader()
        self.ui.setupUi(self.win)
        self.win.setFixedSize(self.win.size())
        self.app.theming.init_on_window(self.win, self.app.dark)
        self.app.styling.apply_on_win(self.win, self.ui, self.app.dark)
        self.ui.logList.setAutoScroll(True)
        self.ui.fetchButton.clicked.connect(self.fetch_info)
        self.ui.downButton.clicked.connect(self.download)
        self.ui.stopButton.clicked.connect(self.stop)
        # TODO: remove
        self.ui.urlEdit.setText('https://www.twitch.tv/videos/2544331339?filter=archives&sort=time')
        self.win.show()

    def stop(self) -> None:
        self.ui.stopButton.setEnabled(False)
        self.downloader.should_stop = True

    def download(self) -> None:
        chunk_size = 10
        self.log_clear()
        self.ui.downBar.setValue(0)
        try:
            chunk_url = self.ui.chunkEdit.text().strip()
            if chunk_url.endswith('.ts') or chunk_url.endswith('.mp4'):
                chunk_url = '/'.join(chunk_url.split('/')[:-1])
            if not chunk_url:
                raise RuntimeError('Invalid chunk URL')
            if not chunk_url.endswith('/'):
                chunk_url += '/'
            writer = SimpleWriter('test.mp4')
        except Exception as err:
            self.log_msg(f'Failed to prepare for writing: {err}')
            return
        sc = math.floor(self.ui.startTime.time().msecsSinceStartOfDay() / (1000 * chunk_size))
        ec = math.ceil(self.ui.endTime.time().msecsSinceStartOfDay() / (1000 * chunk_size))
        if ec <= sc:
            ec = sc + 24 * 60 * 60 // chunk_size
        self.downloader = SingleDownloader(
            self.app.get_default_headers(),
            writer,
            chunk_url,
            True,
            sc,
            ec
        )
        self.downloader.writer = writer
        self.log_msg(f'Chunk URL: {self.downloader.chunk_url}')
        self.log_msg(f'Start chunk: {self.downloader.start_chunk}')
        self.log_msg(f'End chunk: {self.downloader.end_chunk}')
        self.downloader.progress.connect(self.on_down_progress)
        self.locks += 1
        self.set_info_enabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.downBar.setMaximum(self.downloader.end_chunk - self.downloader.start_chunk)
        self.downloader.start()

    def on_down_progress(self, code: int, text: str) -> None:
        if code == 0:
            self.downloader.writer = None
            self.downloader = None
            self.locks -= 1
            self.set_info_enabled(True)
            self.ui.stopButton.setEnabled(False)
            self.log_msg(f'Stopped for reason: {text}')
        elif code == 1:
            self.log_msg(text)
        elif code == 2:
            self.ui.downBar.setValue(int(text))

    def fetch_info(self) -> None:
        self.log_clear()
        try:
            url = self.ui.urlEdit.text().strip()
            if 'twitch.tv/videos/' not in url:
                raise RuntimeError('Incorrect twitch link')
            vid_id = int(url.split('?')[0].strip('/').split('/')[-1])
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
                if data['video'] is None:
                    raise RuntimeError('Video does not exist')
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
