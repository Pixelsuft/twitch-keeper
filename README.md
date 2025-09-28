# Twitch Keeper
A simple Twitch VOD/Stream Downloader written in Python
## Requirements
 - [GRequests](https://github.com/spyoungtech/grequests) (strongly recommended)
 - [PyQt6](https://pypi.org/project/PyQt6/) (PyQt5 works, however)
 - [FFmpeg](https://ffmpeg.org/) (strongly recommended)
 - [darkdetect](https://github.com/albertosottile/darkdetect) (recommended on non-win32 platforms)
## Running
```shell
python build_ui.py
python main.py
```
## Obtaining VOD chunk URL
1) Open needed VOD in browser
2) Set needed quality
3) Open network section in dev tools
4) Find a request to URL something like 123.ts or 456.mp4 and copy that URL
