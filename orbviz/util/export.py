import datetime as dt
import json
import pathlib

import numpy as np

from orbviz.model.data_models import data_types
import orbviz.visualiser.interface.console as console


def exportData(shell, method):
	if method == data_types.ExportMethod.GEOJSON:
		_exportGEOJSON(shell)
	else:
		console.sendErr('Unrecognised export data type')


def _exportGEOJSON(shell):
	subsat_d, oth_d, sensor_d = shell.data['history'].fetchDataForExport(data_types.ExportMethod('geojson'))
	tstamp_str = dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')
	subsat_json_path = pathlib.Path(f'geojson_subsat_{tstamp_str}.json')
	oth_json_path = pathlib.Path(f'geojson_oth_{tstamp_str}.json')
	sensor_json_path = pathlib.Path(f'geojson_sensor_{tstamp_str}.json')
	with subsat_json_path.open('w') as fp:
		json.dump(subsat_d, fp, cls=JSONEncoder, indent=4)

	with oth_json_path.open('w') as fp:
		json.dump(oth_d, fp, cls=JSONEncoder, indent=4)

	with sensor_json_path.open('w') as fp:
		json.dump(sensor_d, fp, cls=JSONEncoder, indent=4)

	console.send('Finished Exporting GEOJSON files:')
	console.send(f'\tSubsatellite points: {subsat_json_path}')
	console.send(f'\tOTH circle: {oth_json_path}')
	console.send(f'\tSensor projections: {sensor_json_path}')

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		elif isinstance(obj, dt.datetime):
			return obj.isoformat()

		return super().default(obj)