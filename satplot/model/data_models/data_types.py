from enum import Enum
import json
import logging
import pathlib
from typing import Any

import satplot.visualiser.assets.sensors as sensor_asset
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

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
			logger.error("Constellation json is ill-formatted: missing field 'name'")
			raise AttributeError("Constellation json is ill-formatted: missing field 'name'")

		if 'beam_width' not in data.keys():
			logger.error("Constellation json is ill-formatted: missing field 'beam_width'")
			raise AttributeError("Constellation json is ill-formatted: missing field 'beam_width'")

		if 'satellites' not in data.keys():
			logger.error("Constellation json is ill-formatted: missing field 'satellites'")
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
			# Check sensor is a valid type
			if v['shape'] not in sensor_asset.Sensor3DAsset.getValidTypes():
				logger.error(f"Sensor {k} of suite {self.name} has invalid shape: {v['shape']}. Should be one of {sensor_asset.Sensor3DAsset.getValidTypes()}")
				raise ValueError(f"Sensor {k} of suite {self.name} has invalid shape: {v['shape']}. Should be one of {sensor_asset.Sensor3DAsset.getValidTypes()}")
			required_keys =  sensor_asset.Sensor3DAsset.getTypeConfigFields(v['shape'])
			for key in required_keys:
				if key not in v.keys():
					logger.error(f"Sensor {k} of suite {self.name} has missing sensor config field: {key}")
					raise KeyError(f"Sensor {k} of suite {self.name} has missing sensor config field: {key}")


	def getSensorNames(self) -> list[str]:
		return list(self.sensors.keys())

	def getSensorConfig(self, sensor_name) -> dict[str, Any]:
		return self.sensors[sensor_name]

	def __eq__(self, other) -> bool:
		if self is None or other is None:
			return False
		if self.name != other.name:
			return False

		if self.sensors != other.sensors:
			return False

		return True

class SpacecraftConfig():
	def __init__(self, filestem:str, name:str, sat_id:int, sensor_suites_dict:dict[str, dict]):
		self.filestem = filestem
		self.name = name
		self.id = sat_id
		self.sensor_suites = {}

		for suite_name, suite in sensor_suites_dict.items():
			self.sensor_suites[suite_name] = SensorSuiteConfig(suite_name, suite)


	def getNumSuites(self) -> int:
		return len(self.sensor_suites)

	def getSensorSuites(self):
		return self.sensor_suites

	def __eq__(self, other) -> bool:
		if self is None or other is None:
			return False
		if self.name != other.name:
			return False

		if self.id != other.id:
			return False

		if self.sensor_suites != other.sensor_suites:
			return False

		return True

class PrimaryConfig():
	def __init__(self, filestem:str, name:str, satellites:dict[int, str], sat_configs:dict[str, SpacecraftConfig]):
		self.filestem = filestem
		self.name = name
		self.sats = satellites
		self.sat_configs = sat_configs

		logger.info(f'Created primary configuration with name:{self.name}, sats:{self.sats}, sat_configs:{self.sat_configs}')

	@classmethod
	def fromJSON(cls, path:str | pathlib.Path):
		if type(path) is str:
			p = pathlib.Path(path)
		else:
			p = path

		with open(p,'r') as fp:
			data = json.load(fp)

		if 'name' not in data.keys():
			logger.error("Primary configuration json is ill-formatted: missing field 'name'")
			raise KeyError("Primary configuration json is ill-formatted: missing field 'name'")

		if 'satellites' not in data.keys():
			logger.error("Primary configuration json is ill-formatted: missing field 'satellites'")
			raise KeyError("Primary configuration json is ill-formatted: missing field 'satellites'")

		sats = {}
		for k,v in data['satellites'].items():
			sat_id = v['id']
			sats[sat_id] = k

		sat_configs = {}
		for k,v in data['satellites'].items():
			if 'sensor_suites' in v.keys():
				sat_configs['k'] = SpacecraftConfig(p.stem, k, v['id'], v['sensor_suites'])
			else:
				logger.debug(f'Spacecraft definition has no sensor suites field.')
				console.send(f'Spacecraft definition has no sensor suites field.')
				sat_configs['k'] = SpacecraftConfig(p.stem, k, v['id'], {})

		return cls(p.stem, data['name'], sats, sat_configs)

	def getSatIDs(self) -> list[int]:
		return list(self.sats.keys())

	def getSatName(self, id:int) -> str:
		return self.sats[id]

	def getSpacecraftConfig(self, id:int) -> SpacecraftConfig:
		return self.sat_configs[self.getSatName(id)]

	def getAllSpacecraftConfigs(self):
		return self.sat_configs

	def __eq__(self, other) -> bool:
		if self is None or other is None:
			return False
		if self.name != other.name:
			return False

		if self.sats != other.sats:
			return False

		if self.sat_configs != other.sat_configs:
			return False

		return True

