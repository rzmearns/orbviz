from enum import Enum
import json
import pathlib
from typing import Any

import satplot.visualiser.assets.sensors as sensor_asset

class DataType(Enum):
	BASE = 1
	HISTORY = 2
	CONSTELLATION = 3

class ConstellationConfig():
	def __init__(self, name:str, beam_width:float, satellites:dict[int, str]):
		self.name = name
		self.beam_width = beam_width
		self.sats = satellites

	@classmethod
	def fromJSON(cls, path:str | pathlib.Path):
		if type(path) is str:
			p = pathlib.Path(path)
		else:
			p = path

		with open(p,'r') as fp:
			data = json.load(fp)

		if 'name' not in data.keys():
			raise AttributeError("Constellation json is ill-formatted: missing field 'name'")

		if 'beam_width' not in data.keys():
			raise AttributeError("Constellation json is ill-formatted: missing field 'beam_width'")

		if 'satellites' not in data.keys():
			raise AttributeError("Constellation json is ill-formatted: missing field 'satellites'")

		# swap key and values of satellites dict
		sats = {}
		for k,v in data['satellites'].items():
			sats[v] = k

		return cls(data['name'], data['beam_width'], sats)

class SensorSuiteConfig():
	def __init__(self, name:str, d:dict):
		self.name = name
		self.sensors = d

		for k,v in self.sensors.items():
			print(k)
			# Check sensor is a valid type
			if v['shape'] not in sensor_asset.Sensor3DAsset.getValidTypes():
				raise ValueError(f"Sensor {k} of suite {self.name} has invalid shape: {v['shape']}. Should be one of {sensor_asset.Sensor3DAsset.getValidTypes()}")
			required_keys =  sensor_asset.Sensor3DAsset.getTypeConfigFields(v['shape'])
			for key in required_keys:
				if key not in v.keys():
					raise KeyError(f"Sensor {k} of suite {self.name} has missing sensor config field: {key}")


	def getSensorNames(self) -> list[str]:
		return list(self.sensors.keys())

	def getSensorConfig(self, sensor_name) -> dict[str, Any]:
		return self.sensors[sensor_name]

class PrimaryConfig():
	def __init__(self, name:str, satellites:dict[int, str], sensor_suites:dict[str, SensorSuiteConfig]):
		self.name = name
		self.sats = satellites
		self.sensor_suites = sensor_suites

		print(f'{self.name=}')
		print(f'{self.sats=}')
		print(f'{self.sensor_suites=}')

	@classmethod
	def fromJSON(cls, path:str | pathlib.Path):
		if type(path) is str:
			p = pathlib.Path(path)
		else:
			p = path

		with open(p,'r') as fp:
			data = json.load(fp)


		if 'name' not in data.keys():
			raise KeyError("Constellation json is ill-formatted: missing field 'name'")

		if 'sensor_suites' not in data.keys():
			raise KeyError("Constellation json is ill-formatted: missing field 'sensor_suites'")

		if 'satellites' not in data.keys():
			raise KeyError("Constellation json is ill-formatted: missing field 'satellites'")

		sats = {}
		for k,v in data['satellites'].items():
			sats[v] = k
		print(f'{sats=}')

		sens_suites = {}
		for sat, suites in data['sensor_suites'].items():
			print(f'{sat=}')
			if sat not in sats.values():
				raise KeyError(f"Sensor suites defined for {sat} not found in primary config")
			for suite_name, suite in suites.items():
				sens_suites[suite_name] = SensorSuiteConfig(suite_name, suite)

		return cls(data['name'], sats, sens_suites)

	def getSatIDs(self) -> list[int]:
		return list(self.sats.keys())
