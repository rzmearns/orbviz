import logging
import os
import pathlib

import typing

satplot_dir = pathlib.Path(f'{os.path.dirname(os.path.abspath(__file__))}').parent.parent.resolve()
data_dir = satplot_dir.joinpath('data')
credential_dir = data_dir.joinpath('spacetrack')
constellation_dir = data_dir.joinpath('constellation_configs')
gifs_dir = data_dir.joinpath('gifs')
prim_cnfg_dir = data_dir.joinpath('primary_configs')
pnt_dir = data_dir.joinpath('pointing')
save_dir = data_dir.joinpath('saves')
screenshot_dir = data_dir.joinpath('screenshots')