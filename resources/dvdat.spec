# -*- mode: python -*-

import os

a = Analysis(['dvdat.py'],
             pathex=['C:\\Users\\jbolzan\\Dropbox\\dvdAT'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

DATA_FILES = []

for filename in os.listdir('graphics'):
    filepath = 'graphics' + '\\' + filename
    if os.path.isfile(filepath) and (filepath.endswith('png') or filepath.endswith('mkv')) and not filepath.startswith('.'):
        DATA_FILES.append(('graphics' + '\\' + filename, filepath, 'DATA'))

for filename in os.listdir('resources'):
    filepath = 'resources' + '\\' + filename
    if os.path.isfile(filepath) and (filepath.endswith('exe') or filepath.endswith('dll') or filepath.endswith('ttf') or filepath.endswith('flac')) and not filepath.startswith('.'):
        DATA_FILES.append((filename, filepath, 'DATA'))

a.datas += DATA_FILES

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='DVD Authoring Tool.exe',
          debug=False,
          strip=None,
          upx=True,
          onefile=True,
          console=False,
          icon='pixmaps\\dvdat.ico')
