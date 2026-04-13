import pathlib

import orbviz

orbviz_dir = pathlib.Path(__file__).parent.parent.parent.resolve()

resources_dir = orbviz_dir.joinpath('resources')
actions_dir = resources_dir.joinpath('actions')
icons_dir = resources_dir.joinpath('icons')

data_dir = orbviz.data_dir
credential_dir = data_dir.joinpath('spacetrack')
constellation_dir = data_dir.joinpath('constellation_configs')
events_dir = data_dir.joinpath('events')
gs_dir = data_dir.joinpath('groundstation_configs')
gifs_dir = data_dir.joinpath('gifs')
logs_dir = data_dir.joinpath('logs')
prim_cnfg_dir = data_dir.joinpath('primary_configs')
att_dir = data_dir.joinpath('attitude')
save_dir = data_dir.joinpath('saves')
export_dir = data_dir.joinpath('exports')
screenshot_dir = data_dir.joinpath('screenshots')

# check dir exist
credential_dir.mkdir(parents=False, exist_ok=True)
constellation_dir.mkdir(parents=False, exist_ok=True)
events_dir.mkdir(parents=False, exist_ok=True)
gs_dir.mkdir(parents=False, exist_ok=True)
gifs_dir.mkdir(parents=False, exist_ok=True)
logs_dir.mkdir(parents=False, exist_ok=True)
prim_cnfg_dir.mkdir(parents=False, exist_ok=True)
att_dir.mkdir(parents=False, exist_ok=True)
save_dir.mkdir(parents=False, exist_ok=True)
export_dir.mkdir(parents=False, exist_ok=True)
screenshot_dir.mkdir(parents=False, exist_ok=True)