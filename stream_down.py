import os
import time
import datetime

import writer

try:
    import grequests  # noqa
    has_grequests = True
except ImportError:
    has_grequests = False
import requests
from ui_main import QtWidgets, QtGui, QtCore
from ui_stream import Ui_StreamDownloaderWindow
from writer import SimpleWriter, FFMPEGWriter

class DownloaderThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int, str)

    def __init__(self, headers: dict, writer, meta_url: str) -> None:
        super().__init__()
        self.headers = headers
        self.writer = writer
        self.meta_url = meta_url
        self.should_stop = False
        self.parallel = has_grequests  # TODO
        self.stime = 0
        self.total_seq = 0

    def run(self) -> None:
        self.stime = time.time()
        err_count = 0
        first = True
        cur_down = 0
        while True:
            if self.should_stop:
                self.progress.emit(0, 'Aborted by user')
                return
            if err_count >= 10:
                self.progress.emit(0, 'Too many errors in a row')
                return
            # TODO: better error handling
            try:
                data = requests.get(self.meta_url, headers=self.headers)
                if not data.status_code == 200:
                    raise RuntimeError(f'Request failed with status code {data.status_code}')
                next_dur = 0
                cur_seq = 0
                urls = []
                for i in data.text.split('\n'):
                    if next_dur:
                        next_dur = 0
                        urls.append(i)
                    if i.startswith('#EXTINF:'):
                        next_dur = float(i[8:].split(',')[0])
                    elif i.startswith('#EXT-X-TWITCH-PREFETCH:'):
                        pass
                        # print(i[23:])
                    elif i.startswith('#EXT-X-TWITCH-LIVE-SEQUENCE:'):
                        cur_seq = int(i[28:])
                        if first:
                            cur_down = cur_seq
                            self.progress.emit(1, f'First chunk: {cur_down}')
                need_count = cur_seq + len(urls) - cur_down
                if need_count > len(urls):
                    self.progress.emit(1, f'Underrun occurred ({need_count - len(urls)} chunks)')
                    need_count = len(urls)
                    cur_down = cur_seq
                elif need_count <= 0:
                    if first:
                        need_count = 0
                        first = False
                    else:
                        self.progress.emit(1, f'Overrun occurred')
                        time.sleep(1.5)
                        continue
                first = False
                urls = urls[-need_count:]
                if self.parallel:
                    # content = b''
                    wt = 0
                    for i in grequests.map([grequests.get(x, headers=self.headers) for x in urls]):
                        if i.status_code == 200:
                            st = time.time()
                            self.writer.write(i.content)
                            wt += time.time() - st
                            # content += i.content
                            self.total_seq += 1
                            self.progress.emit(2, str(self.total_seq % 30))
                        else:
                            self.progress.emit(1, f'Failed to fetch chunk with status code {i.status_code}')
                    # print(f'Time taken: {wt}s')
                    # self.writer.write(content)
                else:
                    for u in urls:
                        i = requests.get(u, headers=self.headers)
                        if i.status_code == 200:
                            self.writer.write(i.content)
                            self.total_seq += 1
                            self.progress.emit(2, str(self.total_seq % 30))
                        else:
                            self.progress.emit(1, f'Failed to fetch chunk with status code {i.status_code}')
                cur_down += need_count
                # last_seq = cur_seq
            except Exception as err:
                err_count += 1
                self.progress.emit(1, f'Failed to download/write data: {err}')

class StreamDown:
    def __init__(self, app) -> None:
        self.app = app
        self.locks = 0
        self.downloader = None
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
        self.ui.ffmpegEdit.setText(writer.get_default_ffmpeg_cmd(True))
        self.win.show()

    def stop(self) -> None:
        self.ui.stopButton.setEnabled(False)
        self.downloader.should_stop = True

    def download(self) -> None:
        self.set_info_enabled(False)
        self.log_clear()
        self.ui.downBar.setValue(0)
        try:
            meta_url = self.ui.metaEdit.text().strip()
            if not meta_url or not meta_url.endswith('.m3u8'):
                raise RuntimeError('Invalid meta URL')
            out_path = self.ui.outEdit.text()
            self.log_msg(f'Output path: {out_path}')
            if not out_path.strip() or (os.path.exists(out_path) and not os.path.isfile(out_path)):
                raise RuntimeError('Invalid output path')
            ffmpeg_cmd = self.ui.ffmpegEdit.text()
            enable_ffmpeg = bool(ffmpeg_cmd.strip())
            if os.path.isfile(out_path):
                os.remove(out_path)
            writer = FFMPEGWriter(ffmpeg_cmd, out_path) if enable_ffmpeg else SimpleWriter(out_path)
        except Exception as err:
            self.log_msg(f'Failed to prepare for writing: {err}')
            self.set_info_enabled(True)
            return
        self.downloader = DownloaderThread(
            self.app.get_default_headers(),
            writer,
            meta_url
        )
        self.downloader.writer = writer
        # self.log_msg(f'Meta URL: {self.downloader.meta_url}')
        self.downloader.progress.connect(self.on_down_progress)
        self.set_info_enabled(False)
        self.ui.stopButton.setEnabled(True)
        self.locks += 1
        self.downloader.start()

    def on_down_progress(self, code: int, text: str) -> None:
        if code == 0:
            now = time.time()
            self.log_msg(f'Finished in: {datetime.timedelta(seconds=now - self.downloader.stime)}')
            self.log_msg(f'Total chunks: {self.downloader.total_seq}')
            self.log_msg(f'Calculated time: {datetime.timedelta(seconds=self.downloader.total_seq * 2)}')
            self.downloader.writer = None
            self.downloader = None
            self.locks -= 1
            self.set_info_enabled(True)
            self.ui.stopButton.setEnabled(False)
            self.log_msg(f'Stop reason: {text}')
        elif code == 1:
            self.log_msg(text)
        elif code == 2:
            time_str = datetime.timedelta(seconds=self.downloader.total_seq * 2)
            # print(time_str)
            self.ui.downBar.setValue(int(text))

    def set_info_enabled(self, enabled: bool):
        self.ui.downButton.setEnabled(enabled)
        self.ui.outButton.setEnabled(enabled)
        self.ui.outEdit.setEnabled(enabled)
        self.ui.ffmpegEdit.setEnabled(enabled)
        self.ui.metaEdit.setEnabled(enabled)

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
