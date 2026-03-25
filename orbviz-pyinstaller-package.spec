# -*- mode: python -*-
import sys
sys.setrecursionlimit(5000)
from PyInstaller.compat import is_win, is_darwin, is_linux
from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_dynamic_libs,
    copy_metadata,
    collect_all
    )
import vispy.glsl
import vispy.io
import freetype

block_cipher = None

data_files = [
    (os.path.dirname(vispy.glsl.__file__), os.path.join("vispy", "glsl")),
    (os.path.join(os.path.dirname(vispy.io.__file__), "_data"), os.path.join("vispy", "io", "_data")),
    (os.path.dirname(vispy.util.__file__), os.path.join("vispy", "util")),
    (os.path.dirname(freetype.__file__), os.path.join("freetype")),
    ('resources', 'resources')
]

hidden_imports = [
    "vispy.ext._bundled.six",
    "vispy.app.backends._pyqt5",
    'vispy.gloo.gl.glplus',
    'vispy.gloo.gl.es2',
    'vispy.ext._gl_ir'
    "freetype",    
]

extra_binaries = []

for pkg in ['imageio', 'astroquery']:
    df, eb, hi = collect_all(pkg)
    data_files += df
    extra_binaries += eb
    hidden_imports += hi

if is_win:
    hidden_imports += collect_submodules("encodings")
    hidden_imports += collect_submodules("PyQT5")

a = Analysis(['application.py'],
             pathex=[],
             datas=data_files,
             hiddenimports=hidden_imports,
             binaries=extra_binaries,
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          [],
          [],
          [],
          exclude_binaries=True,
          name='orbviz',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='orbviz'
)