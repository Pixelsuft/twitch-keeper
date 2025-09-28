import subprocess
import threading

_has_nvidia_cache = -1

def has_nvidia() -> bool:
    global _has_nvidia_cache
    if _has_nvidia_cache == -1:
        try:
            _has_nvidia_cache = subprocess.call(
                ['nvidia-smi'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            ) == 0
        except Exception as _err:
            if _err:
                pass
            _has_nvidia_cache = False
    return bool(_has_nvidia_cache)

def get_default_ffmpeg_cmd(is_stream: bool) -> str:
    ret = 'ffmpeg -i pipe:0 -c:a copy'
    if has_nvidia():
        ret += ' -c:v h264_nvenc'
    elif is_stream:
        ret += ' -vf \'format=nv12,hwupload\' -c:v h264_vaapi'
    else:
        ret += ' -c:v libx264 -threads 0'
    ret += ' %out%'
    return ret

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
        self.direct_write(data)

    def __del__(self) -> None:
        if self.proc.poll() is None:
            if self.buffer:
                self.direct_write(self.buffer)
            self.proc.stdin.close()
            self.proc.wait()
