import datetime as dt
import logging
import pathlib

import typing
from typing import Any, cast

import numpy as np
from numpy import typing as nptyping
from progressbar import progressbar
from scipy.spatial.transform import Rotation
import spherapy.orbit as orbit
import spherapy.timespan as timespan
import spherapy.updater as updater

import satplot
from satplot.model.data_models.base_models import BaseDataModel
import satplot.model.data_models.constellation_data as constellation_data
import satplot.model.data_models.data_types as data_types
import satplot.util.constants as satplot_constants
import satplot.util.threading as threading
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class HistoryData(BaseDataModel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type',data_types.DataType.HISTORY)
		# initialise empty config
		self._setConfig('timespan_period_start', None)
		self._setConfig('timespan_period_end', None)
		self._setConfig('sampling_period', None)
		self._setConfig('pointing_defines_timespan', False)
		self._setConfig('primary_satellite_ids', []) # keys of orbits, position dict
		self._setConfig('primary_satellite_config', None)
		self._setConfig('has_supplemental_constellation', False)
		self._setConfig('num_geolocations', 0)
		self._setConfig('is_pointing_defined', False)
		self._setConfig('pointing_file', None)
		self._setConfig('pointing_invert_transform', False)

		self.timespan: timespan.TimeSpan | None = None
		self.orbits: dict[int, orbit.Orbit] = {}
		self.pointings: dict[int, HistoricalAttitude] = {}
		self.constellation: constellation_data.ConstellationData | None = None
		self.sun: nptyping.NDArray[np.float64] | None = None
		self.moon: nptyping.NDArray[np.float64] | None = None
		self.geo_locations: list[nptyping.NDArray[np.float64]] = []
		self.curr_index:int|None = None
		self._worker_threads: dict[str, threading.Worker | None] = {'primary': None,
																	'constellation': None}
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

	def getPointings(self) -> dict[int, "HistoricalAttitude"]:
		if len(self.pointings.values()) == 0:
			logger.warning('History data:%s has no pointings yet', self)
			raise ValueError(f'History data:{self} has no pointings yet')
		return self.pointings

	def getSCAttitude(self, sc_id:int) -> "HistoricalAttitude":
		return self.pointings[sc_id]

	def process(self) -> None:
		# Load pointing and create timespan
		if self.getConfigValue('is_pointing_defined'):
			for sc_id, sc_config in self.getConfigValue('primary_satellite_config').getAllSpacecraftConfigs().items():
				self.pointings[sc_id] = HistoricalAttitude(self.getConfigValue('pointing_file'), sc_config)
			if self.getConfigValue('pointing_defines_timespan'):
				console.send("Loading timespan from pointing file.")
				_timearr = self.pointings[self.getConfigValue('primary_satellite_ids')[0]].getPointingTimestamps()
				self.timespan = timespan.TimeSpan.fromDatetime(_timearr)
				logger.info('Generating timespan from pointing file timestamps for: %s', self)
			else:
				self.timespan = None

		if self.timespan is None or not self.getConfigValue('is_pointing_defined'):
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


		if self.timespan is None:
			logger.warning("History data:%s, timespan has not been configured", self)
			raise AttributeError(f"History data:{self}, Timespan has not been configured")

		console.send(f"\tDuration: {self.timespan.time_period}")
		console.send(f"\tNumber of steps: {len(self.timespan)}")


		# Set up workers for orbit propagation
		self._worker_threads['primary'] = threading.Worker(self._propagatePrimaryOrbits, self.timespan, self.getConfigValue('primary_satellite_ids'))
		self._worker_threads['primary'].signals.result.connect(self._storeOrbitData)
		self._worker_threads['primary'].signals.finished.connect(self._procComplete)
		self._worker_threads['primary'].signals.error.connect(self._displayError)
		self._worker_threads['primary'].setAutoDelete(True)

		if self.getConfigValue('has_supplemental_constellation'):
			if self.constellation is None:
				logger.warning("History data:%s, constellation has not been configured", self)
				raise AttributeError(f"History data:{self},onstellation has not been configured")

			self.constellation.setTimespan(self.timespan)
			self._worker_threads['constellation'] = threading.Worker(self._propagateConstellationOrbits, self.timespan, self.constellation.getConfigValue('satellite_ids'))
			self._worker_threads['constellation'].signals.result.connect(self.constellation._storeOrbitData)
			self._worker_threads['constellation'].signals.finished.connect(self._procComplete)
			self._worker_threads['constellation'].signals.error.connect(self._displayError)
			self._worker_threads['constellation'].setAutoDelete(True)
		else:
			self._worker_threads['constellation'] = None

		for thread_name, thread in self._worker_threads.items():
			if thread is not None:
				logger.info('Starting thread %s:%s',thread_name, thread)
				satplot.threadpool.logStart(thread)

	def _procComplete(self) -> None:
		logger.info("Thread completion triggered processing of computed data ")
		for thread in self._worker_threads.values():
			if thread is not None:
				if thread.isRunning():
					return
		self.data_ready.emit()


	def _propagatePrimaryOrbits(self, timespan:timespan.TimeSpan, sat_ids:list[int], running:threading.Flag) -> dict[int, orbit.Orbit]:
		updated_list = updater.updateTLEs(sat_ids) 				# noqa: F841
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
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])

		return orbits

	def _propagateConstellationOrbits(self, timespan:timespan.TimeSpan, sat_ids:list[int], running:threading.Flag) -> dict[int, orbit.Orbit]:
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
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])
			ii+=1
		logger.info("\tLoaded %s satellites .", len(sat_ids))
		console.send(f"\tLoaded {len(sat_ids)} satellites .")

		return orbits

	def _storeOrbitData(self, orbits:dict[int,orbit.Orbit]) -> None:
		self.orbits = orbits

	def _createDataPaneEntries(self):
		self.datapane_data.append({'parameter':'Altitude',
						'value':lambda : np.linalg.norm(list(self.orbits.values())[0].pos[self.curr_index,:]) - satplot_constants.R_EARTH,
						'unit':'km'})
		self.datapane_data.append({'parameter':'Eccentricity',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].ecc[self.curr_index,:]),
						'unit':'km'})
		self.datapane_data.append({'parameter':'Inclination',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].inc[self.curr_index,:]),
						'unit':'km'})
		self.datapane_data.append({'parameter':'RAAN',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].raan[self.curr_index,:]),
						'unit':'km'})
		self.datapane_data.append({'parameter':'Argument of Perigee',
						'value':lambda : np.rad2deg(list(self.orbits.values())[0].argp[self.curr_index,:]),
						'unit':'°'})
		self.datapane_data.append({'parameter':'Period Perigee',
						'value':lambda : min(np.linalg.norm(list(self.orbits.values())[0].pos,axis=1) - satplot_constants.R_EARTH),
						'unit':'km'})
		self.datapane_data.append({'parameter':'Period Apogee',
						'value':lambda : max(np.linalg.norm(list(self.orbits.values())[0].pos,axis=1) - satplot_constants.R_EARTH),
						'unit':'km'})
		self.datapane_data.append({'parameter':'Position (ECI)',
						'value':lambda : list(self.orbits.values())[0].pos[self.curr_index,:],
						'unit':'km'})
		self.datapane_data.append({'parameter':'Lat, Long',
						'value':lambda : (list(self.orbits.values())[0].lat[self.curr_index],list(self.orbits.values())[0].lon[self.curr_index]),
						'unit':'°'})
		self.datapane_data.append({'parameter':'Position (ECEF)',
						'value':lambda : list(self.orbits.values())[0].pos_ecef[self.curr_index,:],
						'unit':'km'})
		self.datapane_data.append({'parameter':'Velocity',
						'value':lambda : np.linalg.norm(list(self.orbits.values())[0].vel[self.curr_index,:]),
						'unit':'m/s'})
		self.datapane_data.append({'parameter':'Velocity Vector (ECI)',
						'value':lambda : list(self.orbits.values())[0].vel[self.curr_index,:],
						'unit':'m/s'})
		self.datapane_data.append({'parameter':'Quaternion',
						'value':lambda : list(self.pointings.values())[0][self.curr_index,:],
						'unit':'quat'})

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['timespan'] = self.timespan
		state['orbits'] = self.orbits
		state['pointings'] = self.pointings
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
		self.pointings = state['pointings']
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


def date_parser(d_bytes) -> dt.datetime:
	d_bytes = d_bytes[:d_bytes.index(b'.')+4]
	s = d_bytes.decode('utf-8')
	d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
	d = d.replace(tzinfo=dt.timezone.utc)
	return d.replace(microsecond=0)


class HistoricalAttitude:
	def __init__(self, p_file: pathlib.Path, sc_config:data_types.SpacecraftConfig, quat_defn_direction:str='eci2bf'):
		self.sc_config = sc_config
		self._timestamps, self._sc_raw_quats = self._loadPointingFile(p_file)
		num_samples = len(self._timestamps)
		self._attitude_quats:np.ndarray[tuple[int,int],np.dtype[np.float64]] = np.zeros(self._sc_raw_quats.shape, dtype=np.float64)
		self._sens_attitude_quats:dict[tuple[str,str],np.ndarray[tuple[int,int],np.dtype[np.float64]]] = {}

		self._cached_sc_idx = np.full((num_samples),False)
		self._attitude_matrix_cache:np.ndarray[tuple[int,int,int],np.dtype[np.float64]] = np.zeros((num_samples,3,3), dtype=np.float64)
		self._cached_sens_idx:dict[tuple[str,str], np.ndarray[tuple[int],np.dtype[np.bool_]]] = {}
		self._sens_attitude_matrix_cache:dict[tuple[str,str], np.ndarray[tuple[int,int],np.dtype[np.float64]]] = {}

		# TODO: set standard transform direction as eci2bf
		if quat_defn_direction == 'eci2bf':
			self._invert_transform = True
			self._attitude_quats = self._sc_raw_quats
		elif quat_defn_direction == 'bf2eci':
			self._invert_transform = False
			self._attitude_quats = self._sc_raw_quats
			self._attitude_quats[:,3] *= -1

		for suite_name, suite_config in sc_config.getSensorSuites().items():
			for sens_name in suite_config.getSensorNames():
				sens_bf_quat = suite_config.getSensorBodyQuat(sens_name)
				sens_key = (suite_name, sens_name)
				self._sens_attitude_quats[sens_key] = self._quatArrMult(self._attitude_quats, np.tile(sens_bf_quat,(num_samples,1)))
				self._cached_sens_idx[sens_key] = np.full((num_samples),False)
				self._sens_attitude_matrix_cache[sens_key] = np.zeros((num_samples,3,3), dtype=np.float64)


	def getPointingTimestamps(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._timestamps

	def _loadPointingFile(self, p_file: pathlib.Path) -> tuple[np.ndarray[tuple[int], np.dtype[np.datetime64]], np.ndarray[tuple[int,int],np.dtype[np.float64]]]:
		pointing_q = np.array(())
		pointing_w = np.genfromtxt(p_file, delimiter=',', usecols=[1], skip_header=1).reshape(-1,1)
		pointing_x = np.genfromtxt(p_file, delimiter=',', usecols=[2], skip_header=1).reshape(-1,1)
		pointing_y = np.genfromtxt(p_file, delimiter=',', usecols=[3], skip_header=1).reshape(-1,1)
		pointing_z = np.genfromtxt(p_file, delimiter=',', usecols=[4], skip_header=1).reshape(-1,1)
		pointing_q = np.hstack((pointing_x,pointing_y,pointing_z,pointing_w))
		pointing_dates = np.genfromtxt(p_file, delimiter=',', usecols=[0],skip_header=1, converters={0:date_parser})

		return pointing_dates, pointing_q

	def isAttitudeValid(self, idx:int) -> bool:
		if np.any(np.isnan(self._attitude_quats[idx,:])):
			return False
		return True

	def getAttitudeQuat(self, *args:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		if len(args) > 0:
			return self._attitude_quats[args[0],:]
		return self._attitude_quats

	def getAttitudeMatrix(self, idx:int) -> np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		cache_key = idx
		if self._cached_sc_idx[cache_key]:
			return self._attitude_matrix_cache[cache_key,:,:]
		else:
			if self.isAttitudeValid(idx):
				rot_mat = Rotation.from_quat(self._attitude_quats[idx,:]).as_matrix()
			else:
				rot_mat = np.eye(3)
			self._cached_sc_idx[cache_key] = True
			self._attitude_matrix_cache[cache_key,:,:] = rot_mat
			cast("np.ndarray[tuple[int,int], np.dtype[np.float64]]",rot_mat)
			return rot_mat

	def getSensorAttitudeQuat(self, suite_name:str, sens_name:str, *args:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		if len(args) > 0:
			return self._sens_attitude_quats[(suite_name,sens_name)][args[0],:]
		return self._sens_attitude_quats[(suite_name,sens_name)]

	def getSensorAttitudeMatrix(self, suite_name:str, sens_name:str, idx:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		sens_key = (suite_name, sens_name)
		cache_key = idx
		if self._cached_sens_idx[sens_key][cache_key]:
			return self._sens_attitude_matrix_cache[sens_key][cache_key,:,:]
		else:
			rot_mat = Rotation.from_quat(self._sens_attitude_quats[sens_key][idx,:]).as_matrix()
			self._cached_sens_idx[sens_key][idx] = True
			self._sens_attitude_matrix_cache[sens_key][cache_key,:,:] = rot_mat
			return rot_mat

	def _quatMult(self, q1,q2):
		"""Multiples two quaternions

		Multiplies two quaternions, R and S
		All quaternions need to be supplied in (x,y,z,w)

		#T = R*S
		#Tw = (Rw*Sw − Rx*Sx − Ry*Sy − Rz*Sz)
		#Tx = (Rw*Sx + Rx*Sw − Ry*Sz + Rz*Sy)
		#Ty = (Rw*Sy + Rx*Sz + Ry*Sw − Rz*Sx)
		#Tz = (Rw*Sz − Rx*Sy + Ry*Sx + Rz*Sw)

		Args:
			q1 (ndarray(4,)):
			q2 (ndarray(4,)):

		Returns:
			ndarray(4,): resulting quaternion
		"""

		w = q1[3]*q2[3]-q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]
		x = q1[3]*q2[0]+q1[0]*q2[3]+q1[1]*q2[2]-q1[2]*q2[1]
		y = q1[3]*q2[1]-q1[0]*q2[2]+q1[1]*q2[3]+q1[2]*q2[0]
		z = q1[3]*q2[2]+q1[0]*q2[1]-q1[1]*q2[0]+q1[2]*q2[3]
		return np.array((x,y,z,w))

	def _quatArrMult(self, q1_arr, q2_arr):
		res_q_arr = np.zeros((len(q1_arr),4))
		res_q_arr[:,3] = q1_arr[:,3]*q2_arr[:,3]-q1_arr[:,0]*q2_arr[:,0]-q1_arr[:,1]*q2_arr[:,1]-q1_arr[:,2]*q2_arr[:,2]
		res_q_arr[:,0] = q1_arr[:,3]*q2_arr[:,0]+q1_arr[:,0]*q2_arr[:,3]+q1_arr[:,1]*q2_arr[:,2]-q1_arr[:,2]*q2_arr[:,1]
		res_q_arr[:,1] = q1_arr[:,3]*q2_arr[:,1]-q1_arr[:,0]*q2_arr[:,2]+q1_arr[:,1]*q2_arr[:,3]+q1_arr[:,2]*q2_arr[:,0]
		res_q_arr[:,2] = q1_arr[:,3]*q2_arr[:,2]+q1_arr[:,0]*q2_arr[:,1]-q1_arr[:,1]*q2_arr[:,0]+q1_arr[:,2]*q2_arr[:,3]
		return res_q_arr