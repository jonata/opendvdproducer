# -*- mode: python -*-
block_cipher = None

a = Analysis(['opendvdproducer.py'],
    pathex=['/Users/admin/Documents/opendvdproducer'],
    binaries=None,
    datas=[
        ( 'graphics/*.png', 'graphics' ),
        ( 'graphics/*.mkv', 'graphics' ),
        ( 'resources/libvlccore.8.dylib', 'resources' ),
        ( 'resources/libvlc.5.dylib', 'resources' ),
        ( 'resources/*.ttf', 'resources' ),
        ( 'resources/plugins_mac/*', 'resources/plugins_mac' ),
        ( 'resources/convert', 'resources' ),
        ( 'resources/dvdauthor', 'resources' ),
        ( 'resources/ffmpeg', 'resources' ),
        ( 'resources/ffprobe', 'resources' ),
        ( 'resources/libfontconfig.1.dylib', 'resources' ),
        ( 'resources/libfreetype.6.dylib', 'resources' ),
        ( 'resources/libintl.8.dylib', 'resources' ),
        ( 'resources/libMagickCore-6.Q16.1.dylib', 'resources' ),
        ( 'resources/libMagickWand-6.Q16.1.dylib', 'resources' ),
        ( 'resources/libpng16.16.dylib', 'resources' ),
        ( 'resources/mkisofs', 'resources' ),
        ( 'resources/spumux', 'resources' ),
    ],
    hiddenimports=['vlc'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
    cipher=block_cipher)

exe = EXE(pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=True,
    name='Open DVD Producer',
    debug=False,
    strip=False,
    onefile=False,
    upx=True,
    icon='pixmaps/opendvdproducer.icns',
    console=False )

app = BUNDLE(exe,
    name='Open DVD Producer.app',
    icon='pixmaps/opendvdproducer.icns',
    bundle_identifier='org.jonata.OpenDVDProducer')
