import sys
import ctypes
if sys.platform == 'win32':
    from ctypes import wintypes
else:
    import darkdetect


class Theming:
    def __init__(self) -> None:
        if sys.platform == 'win32':
            build_num = sys.getwindowsversion().build
            self.ux_theme = ctypes.windll.uxtheme
            if build_num >= 17763:
                self.ShouldAppsUseDarkMode = self.ux_theme.__getitem__(132)
                self.ShouldAppsUseDarkMode.argtypes = ()
                self.ShouldAppsUseDarkMode.restype = ctypes.c_bool
                self.AllowDarkModeForWindow = self.ux_theme.__getitem__(133)
                self.AllowDarkModeForWindow.argtypes = (wintypes.HWND, ctypes.c_bool)
                self.AllowDarkModeForWindow.restype = None
            else:
                self.ShouldAppsUseDarkMode = None
                self.AllowDarkModeForWindow = None
            if 17763 <= build_num < 18362:
                self.AllowDarkModeForApp = self.ux_theme.__getitem__(135)
                self.AllowDarkModeForApp.argtypes = ()
                self.AllowDarkModeForApp.restype = None
            else:
                self.AllowDarkModeForApp = None
            if build_num >= 18362:
                self.SetPreferredAppMode = self.ux_theme.__getitem__(135)
                self.SetPreferredAppMode.argtypes = (ctypes.c_int, )
                self.SetPreferredAppMode.restype = ctypes.c_int
            else:
                self.SetPreferredAppMode = None
            if self.AllowDarkModeForApp:
                self.AllowDarkModeForApp()
            if self.SetPreferredAppMode:
                self.SetPreferredAppMode(1)

    def init_on_window(self, win) -> None:
        if not sys.platform == 'win32':
            return
        hwnd = int(win.winId())
        if not hwnd:
            return
        # I don't think I should use SetWindowCompositionAttributeFunc for dark mode cuz Qt done similar for us
        self.AllowDarkModeForWindow(hwnd, True)

    def is_dark(self) -> bool:
        if not sys.platform == 'win32':
            return darkdetect.isDark()
        if self.ShouldAppsUseDarkMode:
            return self.ShouldAppsUseDarkMode()
        return False
