import os

a = Analysis(['opendvdproducer.py'],
             pathex=['C:\\Users\\jbolzan\\Dropbox\\Projects\\opendvdproducer'],
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
        DATA_FILES.append((filepath, filepath, 'DATA'))

    if filename == 'plugins':
        for directory in os.listdir(filepath):
            for dll in os.listdir(filepath + '\\' + directory)
                DATA_FILES.append((filepath + '\\' + directory + '\\' + dll, filepath + '\\' + directory + '\\' + dll, 'DATA'))

a.datas += DATA_FILES

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='Open DVD Producer.exe',
          strip=None,
          upx=True,
          onefile=True,
          console=True,
          debug=True,
          icon='pixmaps\\opendvdproducer.ico')
