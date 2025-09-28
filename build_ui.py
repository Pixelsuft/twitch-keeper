import os
import sys
import subprocess
try:
    from PyQt6 import QtWidgets  # noqa
    is_qt6 = not any(x.lower() == '--qt5' for x in sys.argv[1:])
except ImportError:
    is_qt6 = False

for i in ('main', 'vod', 'stream', 'sets', 'about'):
    if os.path.isfile(f'ui_{i}.py'):
        os.remove(f'ui_{i}.py')
    if is_qt6:
        subprocess.call(['pyuic6', '-o', f'ui_{i}.py', f'ui/{i}.ui'])
        continue
    subprocess.call(['pyuic5', '-o', f'ui_{i}.py', f'ui/{i}.ui'])
    data = open(f'ui_{i}.py', 'r', encoding='utf-8').read().split('\n')
    of = open(f'ui_{i}.py', 'w', encoding='utf-8')
    # print(i)
    for line in data:
        if '::' in line:
            # WTF
            # print(line)
            continue
        of.write(line + '\n')
    of.close()
