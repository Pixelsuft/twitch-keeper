import os
import time
import datetime
try:
    import grequests  # noqa
    has_grequests = True
except ImportError:
    has_grequests = False
import requests
from PyQt6 import QtWidgets, QtGui, QtCore
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
        first = True
        last_seq = 0
        err_count = 0
        last_len = 0  # FIXME
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
                            last_seq = cur_seq
                            self.progress.emit(1, f'First chunk: {cur_seq}')
                print(len(urls))
                delta = cur_seq - last_seq
                # FIXME: ???
                delta -= len(urls) - last_len
                last_len = len(urls)
                if delta > len(urls):
                    self.progress.emit(1, f'Underrun occurred ({delta - len(urls)} chunks)')
                    delta = len(urls)
                elif delta <= 0:
                    if first:
                        delta = len(urls)
                        first = False
                    else:
                        self.progress.emit(1, f'Overrun occurred')
                        time.sleep(1.5)
                        continue
                urls = urls[-delta:]
                if self.parallel:
                    # content = b''
                    for i in grequests.map([grequests.get(x, headers=self.headers) for x in urls]):
                        if i.status_code == 200:
                            self.writer.write(i.content)
                            # content += i.content
                            self.total_seq += 1
                            self.progress.emit(2, str(self.total_seq % 30))
                        else:
                            self.progress.emit(1, f'Failed to fetch chunk with status code {i.status_code}')
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
                last_seq += delta
                # last_seq = cur_seq
            except Exception as err:
                err_count += 1
                self.progress.emit(1, f'Failed to download data: {err}')

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
        self.ui.ffmpegEdit.setText('ffmpeg -i pipe:0 %out%')
        # TODO: remove
        self.ui.outEdit.setText('test.mp4')
        self.ui.metaEdit.setText('https://eus21.playlist.ttvnw.net/v1/playlist/CsAIMbl4cO7T_R_4zw5ziKqGZEBskozXtZCzMJWvwF0BquSjvDkrxqCKFeWmo3y4qCRns7S9KsvM9KMvi1NOhLMG_tDExPblohCF5XMRUe2RLP7Jyi6-kRjoSmLdYbdN2x5KPfIuG33VL5OV-SZ5-z39rfa42cgk9sUb1o9roSE-sWbaGILUBpQcnqJvJh9_UXriKMZ0x-koTuo_5beX9neQW48FBJjBZzAARDKqnFJ61aseQfZJNZGXrzCb22ArnM54tCF4Axfw5QG22Ck4nQfLtsJIZ11z0kX_2qNyOzegbc579y6AMGs3Y2xJIqpLLXssx6T6AGsTrqoxf4u5DA1d6ywRjAV91LdaD5_PusgLHDJhXHmg3uxCQKKNJwkcwKpI-4a85APZiUKcQzU1R39-3wJIuCxllaXRccUK_hnaxRAH0tHln99QTCPI7JcXt9hPip9hDvmw6IU9iR9f8z8XmtCeDeqxeLNTjQ_YYQKh5RDM65KQ8uI5iHamDMJjX2-bTJKT_RmFoAjCHF33yIsGOmcdzBd1W5Fg-4-TIMQ3zsSLUWqXagFyIFFRpgQWnqi3V6wUslfumwzC2YDhnUWijVFsV5iW3e5cSLxMSMWshhEp9VhC1N7YkqV6IpYSbUYs2hqfNqA4Oql3eWA3UCvn9g-w55pM2OM2AUmIwpey2keIx0TSZQzSkJydkpJAafwOQ7dTgH1erEYf7Zbhnyl6XR-KF9dIRB-EYm_btgz6c0y1opRbgNpG4k8pFW_dJt6-SA1Ud8FjHl5LOxAXSD_UTJBsaCHHr32CJz-Wb9CZauXIirsV-mdh9kSa8rOO7dHTUVp1TSGTnRG9L_hDgHMM25XwjfbVTi8SWbQWa8zNJIggAVlBOwEVDOKevOwGsWUzyLjLGba0j0UJvCmJFL6Dh9onUq_K4_sHKCfl_XX5bC-mh5X2NCA0Yb_0GnkUpsTNrx1ZQ5Ka97lyl1ZkGps9PZrMKhnukOAElGGpVd6IQr3oYKKDK8IiCtNm2T8ICW4CTsFjLIGwVH1P6_jauW_6Rp0Jl1UKNSIEK-gbaWZX5-Ou99C0ynZr06_ri3mc0Pss4YFq4oGRk4YSEwSBPvNcCe-6vdSWV9Xz41i5JwTxs0y4X-1aPSggGGkAxxxh03Hldcfbt55zRaFNEIR08oALQcsWcPYJw9SL5zQrDjShjCMhF-reOP0occdn3IUzxh-784J6uUO93DQpfK7vit8i_w_w_CR76L4a4oKdIxI_fwjtAMI3D5qBWL2OAY-pO7eHAoR3lnF4fKHPdMe0Gf3DRh0CacJn2uNpnqufiymCMVXENg-5nNpZRZCId6XM1W2RU8EPD8PmP3s5iA_ezO2C1PAPAcgLgrYERodnarJDWEzPbdGXyINbr1hPGFV9N9h67I6uzlOPjZpYsH3bQwzGB8mbb0R4SvA6peZehFRZJgEaDCEJAhewLOgLVbaPvCABKglldS13ZXN0LTIwlA0.m3u8')
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
