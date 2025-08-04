import logging
import pathlib

import typing

satplot_dir = pathlib.Path(__file__).parent.parent.parent.resolve()
resources_dir = satplot_dir.joinpath('resources')
actions_dir = resources_dir.joinpath('actions')
icons_dir = resources_dir.joinpath('icons')
data_dir = satplot_dir.joinpath('data')
credential_dir = data_dir.joinpath('spacetrack')
constellation_dir = data_dir.joinpath('constellation_configs')
events_dir = data_dir.joinpath('events')
gs_dir = data_dir.joinpath('ground_stations')
gifs_dir = data_dir.joinpath('gifs')
prim_cnfg_dir = data_dir.joinpath('primary_configs')
pnt_dir = data_dir.joinpath('pointing')
save_dir = data_dir.joinpath('saves')
screenshot_dir = data_dir.joinpath('screenshots')