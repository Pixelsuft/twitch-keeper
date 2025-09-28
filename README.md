# Twitch Keeper
A simple Twitch VOD/Stream Downloader written in Python
## Requirements
 - [PyQt6](https://pypi.org/project/PyQt6/) (PyQt5 works, however)
 - [GRequests](https://github.com/spyoungtech/grequests) (strongly recommended)
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
4) Find a request to URL something like 123.ts or 456.mp4 and copy that URL (use .ts or .mp4 filter to find)
## Obtaining stream metadata URL
1) Open needed stream in browser
2) Set needed quality
3) Open network section in dev tools
4) Find a request to URL which ends with .m3u8 and copy that URL (use .m3u8 filter to find)
### FFmpeg note
Using FFmpeg without a hardware acceleration to download a stream will likely result in underruns
