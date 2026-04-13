import datetime as dt
import json

import numpy as np

from orbviz.model.data_models import data_types
import orbviz.util.paths as orbviz_paths
import orbviz.visualiser.interface.console as console


def exportData(shell, method):
	if method == data_types.ExportMethod.GEOJSON:
		_exportGEOJSON(shell)
	else:
		console.sendErr('Unrecognised export data type')


def _exportGEOJSON(shell):
	data = shell.data['history'].fetchDataForExport(data_types.ExportMethod('geojson'))
	for sc_id in data.keys():
		tstamp_start_str = data[sc_id]['period_start'].strftime('%Y-%m-%d-%H%M%SZ')
		tstamp_end_str = data[sc_id]['period_end'].strftime('%Y-%m-%d-%H%M%SZ')
		timestep_str = f"{data[sc_id]['timestep']}S"
		sat_name_str = f"{data[sc_id]['sc_name'].replace(' ','_')}-{data[sc_id]['sc_id']}"
		subsat_json_path = orbviz_paths.export_dir.joinpath(f'{sat_name_str}_subsat_{tstamp_start_str}_{tstamp_end_str}_{timestep_str}.geojson')
		oth_json_path = orbviz_paths.export_dir.joinpath(f'{sat_name_str}_oth_{tstamp_start_str}_{tstamp_end_str}_{timestep_str}.geojson')
		sensor_json_path = orbviz_paths.export_dir.joinpath(f'{sat_name_str}_sensor_{tstamp_start_str}_{tstamp_end_str}_{timestep_str}.geojson')
		with subsat_json_path.open('w') as fp:
			json.dump(data[sc_id]['nadir_d'], fp, cls=JSONEncoder)

		with oth_json_path.open('w') as fp:
			json.dump(data[sc_id]['oth_d'], fp, cls=JSONEncoder)

		with sensor_json_path.open('w') as fp:
			json.dump(data[sc_id]['sensor_d'], fp, cls=JSONEncoder)

		console.send('Finished Exporting GEOJSON files:')
		console.send(f'\tSubsatellite points: {subsat_json_path}')
		console.send(f'\tOTH circle: {oth_json_path}')
		console.send(f'\tSensor projections: {sensor_json_path}')

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.ndarray):
			return obj.round(4).tolist()
		elif isinstance(obj, dt.datetime):
			return obj.isoformat()

		return super().default(obj)