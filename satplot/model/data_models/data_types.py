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
	PLANETARYRAYCAST = 4
	SPHEREIMAGE = 5

class SensorTypes(Enum):
	CONE = 'cone'
	FPA = 'square_pyramid'

	@classmethod
	def hasValue(cls, value):
		return value in cls._value2member_map_

class ConstellationConfig():
	def __init__(self, filestem:str, name:str, beam_width:float, satellites:dict[int, str]):
		self.filestem:str = filestem
		self.name:str = name
		self.sats:dict[int,str] = satellites
		self.num_sats:int = len(self.sats.keys())
		self.beam_width:float = beam_width

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

		return cls(p.stem, data['name'], data['beam_width'], sats)

class SensorSuiteConfig():
	def __init__(self, name:str, d:dict):
		self.name = name
		self.sensors = {}

		for sensor_name, sensor_config in d.items():
			# Check sensor is a valid type
			if not SensorTypes.hasValue(sensor_config['shape']):
				logger.error(f"Sensor {sensor_name} of suite {self.name} has invalid shape: {sensor_config['shape']}. Should be one of {SensorTypes}")
				raise ValueError(f"Sensor {sensor_name} of suite {self.name} has invalid shape: {sensor_config['shape']}. Should be one of {SensorTypes}")

			sens_dict = {'shape':SensorTypes(sensor_config['shape'])}
			required_keys_types =  self.getSensorTypeConfigFields(sens_dict['shape'])
			for config_key, _type in required_keys_types.items():
				if config_key not in sensor_config.keys():
					logger.error(f"Sensor {sensor_name} of suite {self.name} has missing sensor config field: {config_key}")
					raise KeyError(f"Sensor {sensor_name} of suite {self.name} has missing sensor config field: {config_key}")
				elif config_key == 'shape':
					continue
				else:
					sens_dict[config_key] = self._getDecoder(_type)(sensor_config[config_key])

			self.sensors[sensor_name] = sens_dict

	def _getDecoder(self, x:type):
		# TODO: how to annotate this
		return {
			int: self._decodeAny,
			tuple[int]: self._decodeTupleInt,
			tuple[float]: self._decodeTupleFloat
		}.get(x,self._decodeAny)

	def _decodeAny(self, input):
		return input

	def _decodeTupleInt(self, input_str:str) -> tuple:
		t = [int(x) for x in input_str.replace('(','').replace(')','').split(',')]
		return tuple(t)

	def _decodeTupleFloat(self, input_str:str) -> tuple:
		t = [float(x) for x in input_str.replace('(','').replace(')','').split(',')]
		return tuple(t)

	def getSensorNames(self) -> list[str]:
		return list(self.sensors.keys())

	def getNumSensors(self) -> int:
		return len(self.sensors.keys())

	def getSensorConfig(self, sensor_name) -> dict[str, Any]:
		return self.sensors[sensor_name]

	def getSensorDisplayConfig(self, sensor_name) -> dict[str,str]:
		sens_config = self.getSensorConfig(sensor_name)
		type = sens_config['shape']
		if type == SensorTypes.CONE:
			return {'type':str(sens_config['shape']),
					'fov':str(sens_config['fov']),
					'range':str(sens_config['range'])}
		elif type == SensorTypes.FPA:
			return 	{'type':str(sens_config['shape']),
					'fov':str(sens_config['fov']),
					'resolution':str(sens_config['resolution']),
					'range':str(sens_config['range'])}
		else:
			return {}

	def __eq__(self, other) -> bool:
		if self is None or other is None:
			return False
		if self.name != other.name:
			return False

		if self.sensors != other.sensors:
			return False

		return True

	@classmethod
	def getSensorTypeConfigFields(cls, type:SensorTypes) -> dict[str,type]:
		if type == SensorTypes.CONE:
			return {'fov':int,
					'range':int,
					'colour':tuple[int],
					'bf_quat':tuple[float]}
		elif type == SensorTypes.FPA:
			return 	{'fov':tuple[float],
					'resolution':tuple[int],
					'range':int,
					'colour':tuple[int],
					'bf_quat':tuple[float]}
		else:
			return {}

class SpacecraftConfig():
	def __init__(self, filestem:str, name:str, sat_id:int, sensor_suites_dict:dict[str, dict]):
		self.filestem:str = filestem
		self.name:str = name
		self.id:int = sat_id
		self.sensor_suites:dict[str,SensorSuiteConfig] = {}

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
		self.filestem:str = filestem
		self.name:str = name
		self.sats:dict[int,str] = satellites
		self.num_sats:int = len(self.sats.keys())
		self.sat_configs:dict[int,SpacecraftConfig] = sat_configs

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
				sat_configs[k] = SpacecraftConfig(p.stem, k, v['id'], v['sensor_suites'])
			else:
				logger.debug(f'Spacecraft definition has no sensor suites field.')
				console.send(f'Spacecraft definition has no sensor suites field.')
				sat_configs[k] = SpacecraftConfig(p.stem, k, v['id'], {})

		return cls(p.stem, data['name'], sats, sat_configs)

	def getSatIDs(self) -> list[int]:
		return list(self.sats.keys())

	def getSatName(self, id:int) -> str:
		return self.sats[id]

	def getSpacecraftConfig(self, id:int) -> SpacecraftConfig:
		return self.sat_configs[self.getSatName(id)]

	def getAllSpacecraftConfigs(self):
		return self.sat_configs

	def serialiseAllSensors(self) -> dict:
		sens_dict = {}
		for sat_name, sat_config in self.sat_configs.items():
			sat_suites = {}
			for suite_name, suite in sat_config.sensor_suites.items():
				sat_suites[suite_name] = {}
				for sens_name, sens_config in suite.sensors.items():
					sat_suites[suite_name][sens_name] = sens_config

			sens_dict[sat_config.id] = (sat_name, sat_suites)

		return sens_dict

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

