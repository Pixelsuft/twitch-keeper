import os
import subprocess
import signal

class SimpleWriter:
    def __init__(self, path: str) -> None:
        self.file = open(path, 'wb')

    def write(self, data: bytes) -> None:
        self.file.write(data)

    def __del__(self) -> None:
        self.file.close()
        self.file = None

class FFMPEGWriter:
    def __init__(self, cmdline: str, path: str) -> None:
        self.proc = subprocess.Popen(
            cmdline.replace('%out%', '"' + path + '"'),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.PIPE
        )
        self.buffer = b''

    def direct_write(self, data: bytes) -> None:
        try:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except Exception as err:
            raise RuntimeError(err)

    def write(self, data: bytes) -> None:
        if 1:
            self.direct_write(data)
        else:
            if len(self.buffer) < 1024 * 1024 * 10:
                self.buffer += data
                return
            self.direct_write(self.buffer)
            self.buffer = b''

    def __del__(self) -> None:
        if self.proc.poll() is None:
            if self.buffer:
                self.direct_write(self.buffer)
            self.proc.stdin.close()
            self.proc.wait()
