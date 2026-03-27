import httpx
import logging
import pathlib

from typing import Any, cast

import numpy as np
from numpy import typing as nptyping
from progressbar import progressbar
import spherapy.orbit as orbit
import spherapy.timespan as timespan
import spherapy.updater as updater

from orbviz.model.data_models import (
	attitude_data,
	constellation_data,
	data_types,
	event_data,
	groundstation_data,
	sensor_data,
	spacecraft_data,
)
from orbviz.model.data_models.base_models import BaseDataModel
import orbviz.util.constants as orbviz_constants
import orbviz.util.threading as threading
import orbviz.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class HistoryData(BaseDataModel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type',data_types.DataType.HISTORY)
		# initialise empty config
		# configs
		self._setConfig('timespan_period_start', None)
		self._setConfig('timespan_period_end', None)
		self._setConfig('sampling_period', None)
		self._setConfig('primary_satellite_ids', []) # keys of orbits, position dict
		self._setConfig('primary_satellite_config', None)
		self._setConfig('has_supplemental_constellation', False)
		self._setConfig('num_geolocations', 0)
		self._setConfig('attitude_configs', {}) # keys of sc_id
		self._setConfig('events_defined', False)
		self._setConfig('events_file', None)

		# data
		self.timespan: timespan.TimeSpan | None = None
		self.orbits: dict[int, orbit.Orbit] = {}
		self.attitudes: dict[int, attitude_data.HistoricalAttitude] = {}
		# TODO: for multi spacecraft this needs to a dict and properly initiliased
		self.sensor_data: dict[int, sensor_data.SensorData] = {}
		self.sc_data: dict[int, spacecraft_data.SpacecraftData] = {}
		self.constellation: constellation_data.ConstellationData | None = None
		self.events: dict[int, event_data.EventData] | None = None
		self.groundstationCollection: groundstation_data.GroundStationCollection | None = None
		self.sun: nptyping.NDArray[np.float64] | None = None
		self.moon: nptyping.NDArray[np.float64] | None = None
		self.geo_locations: list[nptyping.NDArray[np.float64]] = []
		self.curr_index:int|None = None
		self._worker_manager = threading.WorkerManager()
		self._worker_manager.setAllThreadCompletionFunction(self.data_ready.emit)

		self.datapane_data = []
		self._createDataPaneEntries()
		logger.info("Finished initialising HistoryData")

	def setPrimaryConfig(self, primary_config:data_types.PrimaryConfig) -> None:
		self.updateConfig('primary_satellite_config', primary_config)
		self.updateConfig('primary_satellite_ids', primary_config.getSatIDs())

	def setSupplementalConstellation(self, constellation_config:data_types.ConstellationConfig) -> None:
		self.updateConfig('has_supplemental_constellation', True)
		self.constellation = constellation_data.ConstellationData(constellation_config)

	def clearSupplementalConstellation(self) -> None:
		self.updateConfig('has_supplemental_constellation', False)
		self.constellation = None

	def getTimespan(self) -> timespan.TimeSpan:
		if self.timespan is None:
			logger.warning('History data:%s does not have a timespan yet', self)
			raise ValueError(f'History data:{self} does not have a timespan yet')
		return self.timespan

	def getPrimaryConfig(self) -> data_types.PrimaryConfig:
		return self.getConfigValue('primary_satellite_config')

	def getPrimaryConfigIds(self) -> list[int]:
		return self.getConfigValue('primary_satellite_ids')

	def getConstellation(self) -> constellation_data.ConstellationData:
		if self.constellation is None:
			logger.warning('History data:%s does not have a constellation yet', self)
			raise ValueError(f'History data:{self} does not have a constellation yet')
		else:
			return self.constellation

	def hasOrbits(self) -> bool:
		if len(self.orbits.values()) > 0:
			return True
		else:
			return False

	def getOrbits(self) -> dict[int,orbit.Orbit]:
		if len(self.orbits.values()) == 0:
			logger.warning('History data:%s has no orbits yet', self)
			raise ValueError(f'History data:{self} has no orbits yet')
		return self.orbits

	def getOrbit(self, sc_id:int) -> orbit.Orbit:
		if len(self.orbits.values()) == 0:
			logger.warning('History data:%s has no orbits yet', self)
			raise ValueError(f'History data:{self} has no orbits yet')
		return self.orbits[sc_id]


	def getAttitudes(self) -> dict[int, "attitude_data.HistoricalAttitude"]:
		if len(self.attitudes.values()) == 0:
			logger.warning('History data:%s has no attitudes yet', self)
			raise ValueError(f'History data:{self} has no attitudes yet')
		return self.attitudes

	def getSCAttitude(self, sc_id:int) -> "attitude_data.HistoricalAttitude":
		if len(self.attitudes.values()) == 0:
			logger.warning('History data:%s has no attitudes yet', self)
			raise ValueError(f'History data:{self} has no attitudes yet')
		return self.attitudes[sc_id]

	def getSCData(self, sc_id:int) -> "spacecraft_data.SpacecraftData":
		if len(self.sc_data.values()) == 0:
			logger.warning('History data:%s has no spacecraft data yet', self)
			raise ValueError(f'History data:{self} has no spacecraft data yet')
		return self.sc_data[sc_id]

	def getSCSensorData(self, sc_id:int) -> "sensor_data.SensorData":
		if len(self.sensor_data.values()) == 0:
			logger.warning('History data:%s has no sensor data yet', self)
			raise ValueError(f'History data:{self} has no sensor data yet')
		return self.sensor_data[sc_id]

	def clearData(self):
		self.attitudes = {}
		self.sensor_data = {}
		self.sc_data = {}

	def process(self) -> None:
		# Load attitude and create timespan
		prim_sc_id = list(self.getConfigValue('primary_satellite_config').getAllSpacecraftConfigs().keys())[0]
		# clear attitudes
		self.clearData()
		if self.getConfigValue('attitude_configs')[prim_sc_id].definesTimeSpan():
			# TODO: for multi sat need to pick one?
			for sc_id, sc_config in self.getConfigValue('primary_satellite_config').getAllSpacecraftConfigs().items():
				self.attitudes[sc_id] = attitude_data.HistoricalAttitude.fromAttitudeConfig(sc_config, None, self.getConfigValue('attitude_configs')[sc_id])
			console.send("Loading timespan from attitude file.")
			_timearr = self.attitudes[prim_sc_id].getAttitudeTimestamps()
			self.timespan = timespan.TimeSpan.fromDatetime(_timearr)
			logger.info('Generating timespan from attitude file timestamps for: %s', self)
		else:
			logger.info('Generating timespan from configuration for: %s', self)
			period_start = self.getConfigValue('timespan_period_start').replace(microsecond=0)
			period_end = self.getConfigValue('timespan_period_end').replace(microsecond=0)
			console.send(f"Creating Timespan from {period_start} -> {period_end} ...")
			self.updateConfig('timespan_period_start', period_start)
			self.updateConfig('timespan_period_end', period_end)
			duration = int((self.getConfigValue('timespan_period_end') - self.getConfigValue('timespan_period_start')).total_seconds())
			timestep = self.getConfigValue('sampling_period')
			logger.debug('Timespan has duration:%ss, timestep:%ss, from %s', duration, timestep, period_start)
			# TODO: need field checking here for end before start, etc.
			self.timespan = timespan.TimeSpan(period_start,
								timestep=f'{timestep}S',
								timeperiod=f'{duration}S')

		# Create data models which don't require immediate processing
		for sat_id in [prim_sc_id]:
			self.sensor_data[sat_id] = sensor_data.SensorData(self,
																self.getConfigValue('primary_satellite_config').getSpacecraftConfig(sat_id),
																self.timespan[:])
			self.sc_data[sat_id] = spacecraft_data.SpacecraftData(self,
																self.getConfigValue('primary_satellite_config').getSpacecraftConfig(sat_id),
																self.timespan[:])

		if self.timespan is None:
			logger.warning("History data:%s, timespan has not been configured", self)
			raise AttributeError(f"History data:{self}, Timespan has not been configured")

		console.send(f"\tDuration: {self.timespan.time_period}")
		console.send(f"\tNumber of steps: {len(self.timespan)}")


		# Set up workers for orbit propagation
		self._worker_manager.addWorkerThreadConfig({'thread_name':'primary',
											'processing_fn':self._propagatePrimaryOrbits,
											'processing_args':[self.timespan, self.getConfigValue('primary_satellite_ids')],
											'chain_parent':None,
											'delay_start':False,
											'storage_fn': self._storeOrbitData,
											'error_fn':self._displayError,
											'auto_delete': True})

		if self.getConfigValue('has_supplemental_constellation'):
			if self.constellation is None:
				logger.warning("History data:%s, constellation has not been configured", self)
				raise AttributeError(f"History data:{self}, constellation has not been configured")

			self.constellation.setTimespan(self.timespan)
			self._worker_manager.addWorkerThreadConfig({'thread_name':'constellation',
												'processing_fn':self._propagateConstellationOrbits,
												'processing_args':[self.timespan, self.constellation.getConfigValue('satellite_ids')],
												'chain_parent':None,
												'delay_start':False,
												'storage_fn': self.constellation._storeOrbitData,
												'error_fn':self._displayError,
												'auto_delete': True})

		if self.getConfigValue('events_defined'):
			# Set up event processing thread
			self._worker_manager.addWorkerThreadConfig({'thread_name':'events',
												'processing_fn':self._loadEvents,
												'processing_args':[self.get_configValue('events_file')],
												'chain_parent':'primary',
												'delay_start':True,
												'storage_fn': self._storeEventData,
												'error_fn':self._displayError,
												'auto_delete': True})
		else:
			self.events = None

		self._worker_manager.addWorkerThreadConfig({'thread_name':'groundstations',
											'processing_fn':self._recalculateGroundStations,
											'processing_args':[],
											'chain_parent':'primary',
											'delay_start':True,
											'storage_fn': None,
											'error_fn':self._displayError,
											'auto_delete': True})

		# check if attitudes is already created, otherwise process
		if self.getConfigValue('attitude_configs')[prim_sc_id].is_attitude_defined and not bool(self.attitudes):
			self._worker_manager.addWorkerThreadConfig({'thread_name':'attitudes',
														'processing_fn':self._processAttitudes,
														'processing_args':[],
														'chain_parent':'primary',
														'delay_start':True,
														'storage_fn': self._storeAttitudeData,
														'error_fn':self._displayError,
														'auto_delete': True})


		self._worker_manager.registerWorkerThreads()
		self._worker_manager.start()

	# cross model accessors

	def getSensorTransform(self, sc_id:int, suite_name:str, sens_name:str, timespan_idx:int):
		T = np.eye(4)
		T[0:3, 0:3] = self.getSCAttitude(sc_id).getSensorAttitudeMatrix(suite_name, sens_name, timespan_idx)
		T[0:3, 3] = np.asarray(self.getOrbit(sc_id).pos[timespan_idx]).reshape(-1,3)

		return T

	def _resetCurrIndex(self) -> None:
		# ensure self.curr_index is both within the bounds of the new timespan, and is not None when
		# calculating a new timespan
		logger.info('Setting primary orbit index to 0')
		self.curr_index = 0

	def _propagatePrimaryOrbits(self, timespan:timespan.TimeSpan,
										sat_ids:list[int],
										running:threading.Flag) -> dict[int, orbit.Orbit]:

		reattempt_connection  = True
		attempt_num = 0
		while reattempt_connection and attempt_num < 5:
			try:
				attempt_num += 1
				updated_list = updater.updateTLEs(sat_ids) 				# noqa: F841
				reattempt_connection = False
			except httpx.ConnectError:
				console.sendErr('Could not connect to TLE web source. Potentially using out of date TLEs')
				logger.warning('Could not connect to TLE web source. Potentially using out of date TLEs')
				reattempt_connection = False
			except httpx.ReadTimeout:
				if attempt_num == 1:
					console.send('Fetching a large TLE dataset, this could take a while')
					logger.warning('Fetching a large TLE dataset, this could take a while')

				attempt_num += 1


		# TODO: check number of sats updated == number of sats requested (remove above noqa)
		# if collections.Counter(updated_list) == collections.Counter(self.sat_ids):
		# 		self.finished.emit()
		# 	else:
		# 		self.error.emit

		tle_paths = updater.getTLEFilePaths(sat_ids)
		console.send(f"Propagating orbit from {tle_paths[0].name} ...")
		orbits = {}
		for ii, sat_id in enumerate(sat_ids):
			if not running:
				return orbits
			if tle_paths[ii].exists():
				orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])
			else:
				console.sendErr(f'Could not find TLE file: {tle_paths[ii]}')
				logger.warning('Could not find TLE file: %s', tle_paths[ii])
				raise FileNotFoundError()

		return orbits

	def _propagateConstellationOrbits(self, timespan:timespan.TimeSpan,
											sat_ids:list[int],
											running:threading.Flag) -> dict[int, orbit.Orbit]:
		updated_list = updater.updateTLEs(sat_ids) 				# noqa: F841
		# TODO: check number of sats updated == number of sats requested (remove above noqa)
		# if collections.Counter(updated_list) == collections.Counter(self.sat_ids):
		# 		self.finished.emit()
		# 	else:
		# 		self.error.emit
		tle_paths = updater.getTLEFilePaths(sat_ids)
		orbits = {}
		num_sats = len(sat_ids)
		ii = 0
		for sat_id in progressbar(sat_ids):
			logger.debug('Checking constellation data processing thread flag %s:%s', running, running.getState())
			if not running:

				return orbits
			pc = ii/num_sats*100
			bar_str = int(pc)*'='
			space_str = (100-int(pc))*'  '
			console.send(f'Loading {pc:.2f}% ({ii} of {num_sats}) |{bar_str}{space_str}|\r')
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii], astrobodies=False)
			ii+=1
		logger.info("\tLoaded %s satellites .", len(sat_ids))
		console.send(f"\tLoaded {len(sat_ids)} satellites .")

		return orbits

	def _loadEvents(self, event_file:pathlib.Path,
							running:threading.Flag) -> dict[int, event_data.EventData]:
		event_data_objs = {}
		for sat_id, orbit_data in self.orbits.items():
			if self.timespan is not None:
				event_data_objs[sat_id] = event_data.EventData(event_file, self.timespan, orbit_data)
		return event_data_objs

	def _recalculateGroundStations(self, running:threading.Flag) -> None:
		self.groundstationCollection.updateTimespans(self.timespan)
		console.send("Completed generating ground station location data")
		logger.info("Completed generating ground station location data")

	def _processAttitudes(self, running:threading.Flag) -> None:
		attitudes = {}
		for sat_id, orbit_data in self.orbits.items():
			console.send(f"Generating attitude for {sat_id} ...")
			logger.info("Generating attitude for %s", sat_id)
			sc_config = self.getConfigValue('primary_satellite_config').getSpacecraftConfig(sat_id)
			attitudes[sat_id] = attitude_data.HistoricalAttitude.fromAttitudeConfig(sc_config, orbit_data, self.getConfigValue('attitude_configs')[sat_id])
		console.send("Completed attitude generation")
		logger.info("Completed attitude generation")
		return attitudes

	def _storeOrbitData(self, orbits:dict[int,orbit.Orbit]) -> None:
		logger.info('Storing orbit data')
		self.orbits = orbits
		self._resetCurrIndex()
		self.sun = list(orbits.values())[0].sun_pos
		self.moon = list(orbits.values())[0].moon_pos
		logger.info('Finished storing orbit data')

	def _storeEventData(self, events:dict[int, event_data.EventData]):
		logger.info('Storing event data')
		self.events = events

	def _storeAttitudeData(self, attitudes:dict[int, "attitude_data.HistoricalAttitude"]):
		logger.info('Storing attitude data')
		self.attitudes = attitudes

	def _createDataPaneEntries(self):
		self.datapane_data.append({'parameter':'Altitude',
						'value':lambda : np.linalg.norm(list(self.orbits.values())[0].pos[self.curr_index,:]) - orbviz_constants.R_EARTH,
						'unit':'km',
						'precision':6})
		self.datapane_data.append({'parameter':'Eccentricity',
						'value':lambda : list(self.orbits.values())[0].ecc[self.curr_index],
						'unit':None,
						'precision':6})
		self.datapane_data.append({'parameter':'Inclination',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].inc[self.curr_index]),
						'unit':'°',
						'precision':2})
		self.datapane_data.append({'parameter':'RAAN',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].raan[self.curr_index]),
						'unit':'°',
						'precision':2})
		self.datapane_data.append({'parameter':'Argument of Perigee',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].argp[self.curr_index]),
						'unit':'°',
						'precision':2})
		self.datapane_data.append({'parameter':'Period Perigee',
						'value':lambda : min(np.linalg.norm(list(self.orbits.values())[0].pos,axis=1) - orbviz_constants.R_EARTH),
						'unit':'km',
						'precision':2})
		self.datapane_data.append({'parameter':'Period Apogee',
						'value':lambda : max(np.linalg.norm(list(self.orbits.values())[0].pos,axis=1) - orbviz_constants.R_EARTH),
						'unit':'km',
						'precision':2})
		self.datapane_data.append({'parameter':'Position (ECI)',
						'value':lambda : list(self.orbits.values())[0].pos[self.curr_index,:],
						'unit':'km',
						'precision':2})
		self.datapane_data.append({'parameter':'Lat, Long',
						'value':lambda : (list(self.orbits.values())[0].lat[self.curr_index],list(self.orbits.values())[0].lon[self.curr_index]),
						'unit':'°',
						'precision':2})
		self.datapane_data.append({'parameter':'Position (ECEF)',
						'value':lambda : list(self.orbits.values())[0].pos_ecef[self.curr_index,:],
						'unit':'km',
						'precision':2})
		self.datapane_data.append({'parameter':'Velocity',
						'value':lambda : np.linalg.norm(list(self.orbits.values())[0].vel[self.curr_index,:]),
						'unit':'m/s',
						'precision':2})
		self.datapane_data.append({'parameter':'Velocity Vector (ECI)',
						'value':lambda : list(self.orbits.values())[0].vel[self.curr_index,:],
						'unit':'m/s',
						'precision':2})
		self.datapane_data.append({'parameter':'Quaternion',
						'value':lambda : list(self.attitudes.values())[0].getAttitude(self.curr_index),
						'unit':None,
						'precision':4})

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['timespan'] = self.timespan
		state['orbits'] = self.orbits
		state['attitudes'] = self.attitudes
		if self.constellation is not None:
			state['constellation'] = self.constellation.prepSerialisation()
		else:
			state['constellation'] = None
		state['sun'] = self.sun
		state['moon'] = self.moon
		state['geo_locations'] = self.geo_locations
		state['config'] = self.config

		return state

	def deSerialise(self, state):
		self.timespan = state['timespan']
		self.orbits = state['orbits']
		self.attitudes = state['attitudes']
		if state['constellation'] is not None:
			self.constellation = constellation_data.ConstellationData.emptyForDeSerialisation()
			self.constellation.deSerialise(state['constellation'])
			self.constellation.setTimespan(self.timespan)
		else:
			self.constellation = None
		self.sun = state['sun']
		self.moon = state['moon']
		self.geo_locations = state['geo_locations']
		super().deSerialise(state)

	def fetchDataForExport(self, method) -> tuple[dict,dict,dict]:
		sc_ids = list(self.sensor_data.keys())
		for sc_id in sc_ids:
			d = {}
			d[sc_id] = {}
			d[sc_id]['sc_id'] = sc_id
			d[sc_id]['sc_name'] = str(self.sensor_data[sc_id]._sc_config.name)
			d[sc_id]['period_start'] = self.timespan[0]
			d[sc_id]['period_end'] = self.timespan[-1]
			d[sc_id]['timestep'] = self.timespan.timestep

			d[sc_id]['oth_d'] = {}
			d[sc_id]['oth_d']['type'] = 'FeatureCollection'
			d[sc_id]['oth_d']['features'] = []
			# export spacecraft nadir points
			d[sc_id]['oth_d']['features'] += self.sc_data[sc_ids[0]].exportDataAsGEOJSONFeatures()

			d[sc_id]['nadir_d'] = {}
			d[sc_id]['nadir_d']['type'] = 'FeatureCollection'
			d[sc_id]['nadir_d']['features'] = []
			# export spacecraft nadir points
			d[sc_id]['nadir_d']['features'] += self.exportSubSatelliteAsGEOJSONFeatures(sc_ids[0])


			d[sc_id]['sensor_d'] = {}
			d[sc_id]['sensor_d']['type'] = 'FeatureCollection'
			d[sc_id]['sensor_d']['features'] = []
			# export sensor boundary list
			d[sc_id]['sensor_d']['features'] += self.sensor_data[sc_ids[0]].exportDataAsGEOJSONFeatures()

		return d

	def exportSubSatelliteAsGEOJSONFeatures(self, sc_id) -> list[dict]:
		feature_list = []
		for ii in range(len(self.timespan)):
			d = {}
			d['type'] = 'Feature'
			d['properties'] = {}
			d['properties']['ID'] = 4
			d['properties']['sat_id'] = sc_id
			d['properties']['DateTime'] = self.timespan[ii]
			d['geometry'] = {}
			d['geometry']['type'] = 'Point'
			lon_lat = np.array((self.orbits[sc_id].lon[ii], self.orbits[sc_id].lat[ii]))
			d['geometry']['coordinates'] = lon_lat
			feature_list.append(d)

		return feature_list

