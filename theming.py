import sys
import ctypes
if sys.platform == 'win32':
    from ctypes import wintypes

    class AccentPolicy(ctypes.Structure):
        _fields_ = [
            ("AccentState", wintypes.DWORD),
            ("AccentFlags", wintypes.DWORD),
            ("GradientColor", wintypes.DWORD),
            ("AnimationId", wintypes.DWORD),
        ]

    class WindowCompositionAttributes(ctypes.Structure):
        _fields_ = [
            ("Attribute", wintypes.DWORD),
            ("Data", ctypes.POINTER(AccentPolicy)),
            ("SizeOfData", wintypes.ULONG),
        ]
else:
    import darkdetect
from PyQt6 import QtWidgets


class Theming:
    def __init__(self) -> None:
        if sys.platform == 'win32':
            build_num = sys.getwindowsversion().build
            self.ux_theme = ctypes.windll.uxtheme
            self.user32 = ctypes.windll.user32
            if build_num >= 17763:
                try:
                    self.ShouldAppsUseDarkMode = self.ux_theme.__getitem__(132)
                    self.ShouldAppsUseDarkMode.argtypes = ()
                    self.ShouldAppsUseDarkMode.restype = ctypes.c_bool
                except AttributeError:
                    self.ShouldAppsUseDarkMode = None
                try:
                    self.AllowDarkModeForWindow = self.ux_theme.__getitem__(133)
                    self.AllowDarkModeForWindow.argtypes = (wintypes.HWND, ctypes.c_bool)
                    self.AllowDarkModeForWindow.restype = None
                except AttributeError:
                    self.AllowDarkModeForWindow = None
            else:
                self.ShouldAppsUseDarkMode = None
                self.AllowDarkModeForWindow = None
            if 17763 <= build_num < 18362:
                try:
                    self.AllowDarkModeForApp = self.ux_theme.__getitem__(135)
                    self.AllowDarkModeForApp.argtypes = ()
                    self.AllowDarkModeForApp.restype = None
                except AttributeError:
                    self.AllowDarkModeForApp = None
            else:
                self.AllowDarkModeForApp = None
            if build_num >= 18362:
                try:
                    self.SetPreferredAppMode = self.ux_theme.__getitem__(135)
                    self.SetPreferredAppMode.argtypes = (ctypes.c_int, )
                    self.SetPreferredAppMode.restype = ctypes.c_int
                except AttributeError:
                    self.SetPreferredAppMode = None
            else:
                self.SetPreferredAppMode = None
            if build_num >= 18362:
                try:
                    self.SetWindowCompositionAttribute = self.user32.SetWindowCompositionAttribute
                    self.SetWindowCompositionAttribute.argtypes = (
                        wintypes.HWND, ctypes.POINTER(WindowCompositionAttributes)
                    )
                    self.SetWindowCompositionAttribute.restype = wintypes.BOOL
                except AttributeError:
                    self.SetWindowCompositionAttribute = None
            else:
                self.SetWindowCompositionAttribute = None
            # Enables dark context menu on window
            if self.AllowDarkModeForApp:
                self.AllowDarkModeForApp()
            if self.SetPreferredAppMode:
                self.SetPreferredAppMode(1)

    def init_on_window(self, win: any, dark: bool) -> None:
        if not sys.platform == 'win32':
            return
        hwnd = int(win.winId())
        if not hwnd:
            return
        if self.AllowDarkModeForWindow:
            self.AllowDarkModeForWindow(hwnd, True)
        if self.SetWindowCompositionAttribute:
            data = AccentPolicy(int(dark), 0, 0, 0)
            attr = WindowCompositionAttributes(26, ctypes.pointer(data), ctypes.sizeof(AccentPolicy))
            self.SetWindowCompositionAttribute(hwnd, ctypes.pointer(attr))

    def is_dark(self) -> bool:
        if not sys.platform == 'win32':
            return darkdetect.isDark()
        if self.ShouldAppsUseDarkMode:
            return self.ShouldAppsUseDarkMode()
        return False
