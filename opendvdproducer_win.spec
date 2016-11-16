import os, sys

if sys.platform == 'darwin':
    PATHEX = ['/Users/admin/Documents/opendvdproducer']
    NAME = 'Open DVD Producer'
    ONEFILE = False
    ICON = 'pixmaps' + os.sep + 'opendvdproducer.icns'
else:
    PATHEX = ['C:\\Users\\jbolzan\\Documents\\GitHub\\opendvdproducer']
    NAME = 'Open DVD Producer.exe'
    ONEFILE = True
    ICON = 'pixmaps' + os.sep + 'opendvdproducer.ico'

a = Analysis(['opendvdproducer.py'],
             pathex=PATHEX,
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)

DATA_FILES = []

for filename in os.listdir('graphics'):
    filepath = 'graphics' + os.sep + filename
    if os.path.isfile(filepath) and (filepath.endswith('png') or filepath.endswith('mkv')) and not filepath.startswith('.'):
        DATA_FILES.append(('graphics' + os.sep + filename, filepath, 'DATA'))

for filename in os.listdir('resources'):
    filepath = 'resources' + os.sep + filename

    if os.path.isfile(filepath) and (filepath.endswith('exe') or filepath.endswith('dll') or filepath.endswith('ttf') or filepath.endswith('flac')) and not filepath.startswith('.'):
        DATA_FILES.append((filepath, filepath, 'DATA'))

    if not sys.platform == 'darwin' and filename == 'plugins_win':
        for directory in os.listdir(filepath):
            for dll in os.listdir(filepath + os.sep + directory):
                DATA_FILES.append((filepath + os.sep + directory + os.sep + dll, filepath + os.sep + directory + os.sep + dll, 'DATA'))

a.datas += DATA_FILES

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=NAME,
          strip=None,
          upx=True,
          onefile=ONEFILE,
          console=False,
          debug=False,
          icon=ICON)

app = BUNDLE(exe,
         name='myscript.app',
         icon=None,
         bundle_identifier=None)
