import datetime as dt
import numpy as np
from numpy import typing as nptyping
import pathlib
from progressbar import progressbar

import satplot
from satplot.model.data_models.base_models import (BaseDataModel)
import satplot.util.threading as threading
import satplot.model.data_models.data_types as data_types
import satplot.model.data_models.constellation_data as constellation_data
import satplot.visualiser.interface.console as console
import spherapy.timespan as timespan
import spherapy.orbit as orbit
import spherapy.updater as updater

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

		self.timespan: timespan.Timespan | None = None
		self.orbits: dict[int, orbit.Orbit] = {}
		self.pointings: dict[int, nptyping.NDArray[np.float64]] = {}
		self.constellation: constellation_data.ConstellationData | None = None
		self.sun: nptyping.NDArray[np.float64] | None = None
		self.moon: nptyping.NDArray[np.float64] | None = None
		self.geo_locations: list[nptyping.NDArray[np.float64]] = []

		self._worker_threads: dict[str, threading.Worker | None] = {'primary': None,
																	'constellation': None}

		print("Finished initialising HistoryData")

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
			raise ValueError(f'History data:{self} does not have a timespan yet')
		return self.timespan

	def getPrimaryConfig(self) -> data_types.PrimaryConfig:
		return self.getConfigValue('primary_satellite_config')

	def getConstellation(self) -> constellation_data.ConstellationData:
		if self.constellation is None:
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
			raise ValueError(f'History data:{self} has no orbits yet')
		return self.orbits

	def getPointings(self) -> dict[int, nptyping.NDArray[np.float64]]:
		if len(self.pointings.values()) == 0:
			raise ValueError(f'History data:{self} has no pointings yet')
		return self.pointings

	def process(self) -> None:
		# Load pointing and create timespan
		if self.getConfigValue('is_pointing_defined'):
			pointing_dates, pointing = self._loadPointingFile(self.getConfigValue('pointing_file'))
			self.pointings[self.getConfigValue('primary_satellite_ids')[0]] = pointing
			if self.getConfigValue('pointing_defines_timespan'):
				console.send(f"Loading timespan from pointing file.")
				self.timespan = timespan.TimeSpan.fromDatetime(pointing_dates)
				print(f'Generating timespan from pointing file timestamps for: {self}')
			else:
				self.timespan = None

		if self.timespan is None or not self.getConfigValue('is_pointing_defined'):
			print(f'Generating timespan from configuration for: {self}')
			period_start = self.getConfigValue('timespan_period_start').replace(microsecond=0)
			period_end = self.getConfigValue('timespan_period_end').replace(microsecond=0)
			self.updateConfig('timespan_period_start', period_start)
			self.updateConfig('timespan_period_end', period_end)
			duration = int((self.getConfigValue('timespan_period_end') - self.getConfigValue('timespan_period_start')).total_seconds())
			timestep = self.getConfigValue('sampling_period')
			console.send(f"Creating Timespan from {period_start} -> {period_end} ...")
			print(f'{duration=}')
			print(f'{timestep=}')
			print(f'{period_start=}')
			# TODO: need field checking here for end before start, etc.
			self.timespan = timespan.TimeSpan(period_start,
								timestep=f'{timestep}S',
								timeperiod=f'{duration}S')


		if self.timespan is None:
			raise AttributeError("Timespan has not been configured")

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
				raise AttributeError("Constellation has not been configured")

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
				print(f'Starting thread {thread_name}:{thread}')
				satplot.threadpool.logStart(thread)

	def _procComplete(self) -> None:
		print("TRIGGERED COMPLETION")
		for thread in self._worker_threads.values():
			# print(f'Inside _procComplete {thread_name}:{thread}')
			if thread is not None:
				if thread.isRunning():
					return
		self.data_ready.emit()

	def _loadPointingFile(self, p_file: pathlib.Path) -> tuple[nptyping.NDArray, nptyping.NDArray]:
		pointing_q = np.array(())
		pointing_w = np.genfromtxt(p_file, delimiter=',', usecols=[1], skip_header=1).reshape(-1,1)
		pointing_x = np.genfromtxt(p_file, delimiter=',', usecols=[2], skip_header=1).reshape(-1,1)
		pointing_y = np.genfromtxt(p_file, delimiter=',', usecols=[3], skip_header=1).reshape(-1,1)
		pointing_z = np.genfromtxt(p_file, delimiter=',', usecols=[4], skip_header=1).reshape(-1,1)
		pointing_q = np.hstack((pointing_x,pointing_y,pointing_z,pointing_w))
		pointing_dates = np.genfromtxt(p_file, delimiter=',', usecols=[0],skip_header=1, converters={0:date_parser})

		return pointing_dates, pointing_q

	def _propagatePrimaryOrbits(self, timespan:timespan.TimeSpan, sat_ids:list[int], running:threading.Flag) -> dict[int, orbit.Orbit]:
		updated_list = updater.updateTLEs(sat_ids)
		# TODO: check number of sats updated == number of sats requested
		# if collections.Counter(updated_list) == collections.Counter(self.sat_ids):
		# 		self.finished.emit()
		# 	else:
		# 		self.error.emit

		tle_paths = updater.getTLEFilePaths(sat_ids)
		console.send(f"Propagating orbit from {tle_paths[0].split('/')[-1]} ...")
		orbits = {}
		for ii, sat_id in enumerate(sat_ids):
			if not running:
				return orbits
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])

		return orbits

	def _propagateConstellationOrbits(self, timespan:timespan.TimeSpan, sat_ids:list[int], running:threading.Flag) -> dict[int, orbit.Orbit]:
		updated_list = updater.updateTLEs(sat_ids)
		# TODO: check number of sats updated == number of sats requested
		# if collections.Counter(updated_list) == collections.Counter(self.sat_ids):
		# 		self.finished.emit()
		# 	else:
		# 		self.error.emit
		tle_paths = updater.getTLEFilePaths(sat_ids)
		orbits = {}
		num_sats = len(sat_ids)
		ii = 0
		for sat_id in progressbar(sat_ids):
			print(f'CHECKING FLAG {running}: {running.getState()}')
			if not running:

				return orbits
			pc = ii/num_sats*100
			bar_str = int(pc)*'='
			space_str = (100-int(pc))*'  '
			console.send(f'Loading {pc:.2f}% ({ii} of {num_sats}) |{bar_str}{space_str}|\r')
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])
			ii+=1
		console.send(f"\tLoaded {len(sat_ids)} satellites .")

		return orbits

	def _storeOrbitData(self, orbits:dict[int,orbit.Orbit]) -> None:
		self.orbits = orbits

def date_parser(d_bytes) -> dt.datetime:
	d_bytes = d_bytes[:d_bytes.index(b'.')+4]
	s = d_bytes.decode('utf-8')
	d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
	d = d.replace(tzinfo=dt.timezone.utc)
	return d.replace(microsecond=0)
