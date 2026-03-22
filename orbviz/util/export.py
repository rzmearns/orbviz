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
	data = shell.data['history'].fetchDataForExport(data_types.ExportMethod('geojson'))
	tstamp_str = dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')
	json_path = pathlib.Path(f'geojson_{tstamp_str}.json')
	with json_path.open('w') as fp:
		json.dump(data, fp, cls=JSONEncoder, indent=4)

	console.send(f'Finished Exporting GEOJSON file {json_path}')

class JSONEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.ndarray):
			return obj.tolist()
		elif isinstance(obj, dt.datetime):
			return obj.strftime('%Y-%m-%dT%H:%M:%S')

		return super().default(obj)