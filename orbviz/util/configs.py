import datetime as dt
import logging
import pathlib

from typing import Self

from yaml import CLoader as Loader
from yaml import load

import orbviz.util.paths as orbviz_paths

logger = logging.getLogger(__name__)

dflt_config = None
config = None

class Configuration:
	def __init__(self, config_type:str, config_dict:dict):
		self._config_type = config_type

		# primary config
		self._primary_config_path = self._getConfigValue(config_dict,['scenario-modules', 'primary-configuration', 'path'])

		# constellation
		self._constellation_enabled = self._getConfigValue(config_dict,['scenario-modules','constellation-configuration','enabled'])
		self._constellation_config_path = self._getConfigValue(config_dict,['scenario-modules','constellation-configuration','path'])

		# orbital events
		self._orbital_events_enabled = self._getConfigValue(config_dict,['scenario-modules','orbital-events-configuration','enabled'])
		self._orbital_events_path = self._getConfigValue(config_dict,['scenario-modules','orbital-events-configuration','path'])

		# attitude
		self._attitude_config_path = self._getConfigValue(config_dict,['scenario-modules','attitude-configuration','path'])

		# time period
		self._time_period_manual_definition = self._getConfigValue(config_dict,['scenario-modules','time-period-configuration','manual-definition'])
		self._sampling_period = self._getConfigValue(config_dict,['scenario-modules','time-period-configuration','sampling-period'])
		try:
			self._time_period_start = self._getConfigValue(config_dict,['scenario-modules', 'time-period-configuration', 'start-time'])
		except ValueError:
			logger.error('Could not parse %s as a valid time',self._extractValue(config_dict,['scenario-modules', 'time-period-configuration', 'start-time']))  # noqa: TRY400
			self._time_period_start = dt.datetime.now(tz=dt.timezone.utc)
		try:
			self._time_period_end =   self._getConfigValue(config_dict,['scenario-modules', 'time-period-configuration', 'end-time'])
		except ValueError:
			logger.error('Could not parse %s as a valid time',self._extractValue(config_dict,['scenario-modules', 'time-period-configuration', 'start-time']))  # noqa: TRY400
			self._time_period_end = dt.datetime.now(tz=dt.timezone.utc)

		# ground stations
		self._ground_stations = self._getConfigValue(config_dict,['ground-stations','path'])

	def _getConfigValue(self, raw_config:dict, tree_els: list[str]):
		val = self._extractValue(raw_config, tree_els)
		# print(f'{tree_els}:{val}')
		if val is not None:
			parsed_value = self._parseValue(tree_els[-1], val)
		else:
			parsed_value = None
		return parsed_value

	def _parseValue(self, last_key:str, raw_value):
		if last_key == 'path':
			# assumes all paths are in the data_dir
			if isinstance(raw_value, list):
				return [orbviz_paths.data_dir.joinpath(v) for v in raw_value]
			else:
				return orbviz_paths.data_dir.joinpath(raw_value)
		elif 'time' in last_key:

			# try a now() delta
			if raw_value[:3] == 'now':
				delta_str = raw_value[3:]
				if delta_str[0] == '+':
					delta_sign = 1
				elif delta_str[0] == '-':
					delta_sign = -1

				if delta_str[-1] == 's' or delta_str[-1] == 'S':
					time = dt.datetime.now(tz=dt.timezone.utc) + delta_sign * dt.timedelta(seconds=float(delta_str[1:-1]))
				elif delta_str[-1] == 'm' or delta_str[-1] == 'M':
					time = dt.datetime.now(tz=dt.timezone.utc) + delta_sign * dt.timedelta(minutes=float(delta_str[1:-1]))
				elif delta_str[-1] == 'h' or delta_str[-1] == 'H':
					time = dt.datetime.now(tz=dt.timezone.utc) + delta_sign * dt.timedelta(hours=float(delta_str[1:-1]))
				elif delta_str[-1] == 'd' or delta_str[-1] == 'D':
					time = dt.datetime.now(tz=dt.timezone.utc) + delta_sign * dt.timedelta(days=float(delta_str[1:-1]))
				else:
					time = dt.datetime.now(tz=dt.timezone.utc) + delta_sign * dt.timedelta(seconds=float(delta_str[1:]))
				return time

			# not a now() delta
			# try a timestamp
			valid_time = False
			for dt_format in ['%y-%m-%d %H:%M:%S','%y-%m-%d %H:%M:%z','%y-%m-%dT%H:%M:%S','%y-%m-%dT%H:%M:%S%z']:
				try:
					time = dt.datetime.strptime(raw_value, dt_format)
					valid_time = True
					break
				except ValueError:
					continue

			# can't parse the time field
			if not valid_time:
				raise ValueError(f"Couldn't parse {raw_value} as a time")
		else:
			return raw_value

	def _extractValue(self, raw_config:dict, tree_els:list[str]):
		if self._checkKeyExists(raw_config, tree_els):
			return self._returnValue(raw_config, tree_els)
		else:
			logger.error('%s does not exist in raw_config', tree_els)
			return None

	def _returnValue(self, raw_config:dict, tree_els:list[str]) -> bool:
		if len(tree_els) == 1:
			return raw_config[tree_els[0]]
		else:
			return self._returnValue(raw_config[tree_els[0]], tree_els[1:])

	def _checkKeyExists(self, raw_config:dict, tree_els:list[str]) -> bool:
		if raw_config is None:
			return False
		elif tree_els[0] in raw_config.keys():
			if len(tree_els) == 1:
				return True
			else:
				return self._checkKeyExists(raw_config[tree_els[0]], tree_els[1:])
		else:
			return False

	@property
	def primary_config_path(self) -> pathlib.Path:
		if self._primary_config_path is None:
			return dflt_config.primary_config_path
		return self._primary_config_path

	@property
	def constellation_config_path(self) -> pathlib.Path:
		if self._constellation_config_path is None:
			return dflt_config.constellation_config_path
		return self._constellation_config_path

	@property
	def constellation_enabled(self) -> bool:
		if self._constellation_enabled is None:
			return dflt_config.constellation_enabled
		return self._constellation_enabled

	@property
	def orbital_events_enabled(self) -> bool:
		if self._orbital_events_enabled is None:
			return dflt_config.orbital_events_enabled
		return self._orbital_events_enabled

	@property
	def orbital_events_path(self) -> pathlib.Path:
		if self._orbital_events_path is None:
			return dflt_config.orbital_events_path
		return self._orbital_events_path

	@property
	def time_period_start(self) -> dt.datetime:
		if self._time_period_start is None:
			return dflt_config.time_period_start
		return self._time_period_start

	@property
	def time_period_end(self) -> dt.datetime:
		if self._time_period_end is None:
			return dflt_config.time_period_end
		return self._time_period_end

	@property
	def time_period_manual_definition(self) -> bool:
		if self._time_period_manual_definition is None:
			return dflt_config.time_period_manual_definition
		return self._time_period_manual_definition

	@property
	def sampling_period(self) -> int:
		if self._sampling_period is None:
			return dflt_config.sampling_period
		return self._sampling_period

	@property
	def ground_stations(self) -> list:
		if self._ground_stations is None:
			return dflt_config.ground_stations
		return self._ground_stations

	@property
	def attitude_config_path(self) -> pathlib.Path:
		if self._attitude_config_path is None:
			return dflt_config.attitude_config_path
		return self._attitude_config_path


	@classmethod
	def fromConfigFile(cls, config_type:str, path:pathlib.Path) -> Self:
		with path.open('r') as fp:
			data = load(fp,Loader=Loader)

		return cls(config_type, data)

def loadConfig():
	global config
	global dflt_config
	dflt_config = Configuration.fromConfigFile('dflt', pathlib.Path(orbviz_paths.resources_dir).joinpath('default_orbviz_config.yml'))
	config = Configuration.fromConfigFile('user', pathlib.Path(orbviz_paths.data_dir).joinpath('orbviz_config.yml'))