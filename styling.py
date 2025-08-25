import os
from PyQt6 import QtWidgets


class Styling:
    def __init__(self) -> None:
        self.style = ''
        self.style_light = ''
        self.style_dark = ''

    def read_styles(self, path: str, read_light: bool = True, read_dark: bool = True) -> None:
        self.style = open(os.path.join(path, 'style.qss'), 'r', encoding='utf-8').read()
        if not self.style.endswith('\n'):
            self.style += '\n'
        if read_light:
            self.style_light = open(os.path.join(path, 'light.qss'), 'r', encoding='utf-8').read()
        if read_dark:
            self.style_dark = open(os.path.join(path, 'dark.qss'), 'r', encoding='utf-8').read()

    def apply_on_win(self, win, ui, is_dark: bool) -> None:
        ui.centralwidget.setStyle(QtWidgets.QStyleFactory.create('windowsvista'))
        win.setStyleSheet(self.style + (self.style_dark if is_dark else self.style_light))
