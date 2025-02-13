import numpy as np
import datetime as dt
import sys
import pathlib
import collections

from PyQt5 import QtCore

import satplot
from satplot.model.data_models.base import (BaseDataModel)
import satplot.util.threading as threading
import satplot.model.data_models.data_types as data_types
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
		self._setConfig('has_supplemental_constellation', False)
		self._setConfig('num_geolocations', 0)
		self._setConfig('is_pointing_defined', False)
		self._setConfig('pointing_file', None)
		self._setConfig('pointing_invert_transform', False)

		self.timespan = None
		self.orbits = {}
		self.pointings = {}
		self.constellation = None
		self.sun = None
		self.moon = None
		self.geo_locations = []

		self.worker_threads = {'primary': None,
								'pointing': None,
								'constellation': None,
								'spacetrack': None}

		print("Finished initialising HistoryData")

	def setPrimarySatellites(self, satellite_config):
		self.updateConfig('primary_satellite_ids', list(satellite_config['satellites'].values()))

	def setSupplementalConstellation(self, constellation_config):
		self.updateConfig('has_supplemental_constellation', True)
		self.constellation = ConstellationData(constellation_config)
		raise NotImplementedError()

	def clearSupplementalConstellation(self):
		self.updateConfig('has_supplemental_constellation', False)

	def process(self):
		# Load pointing and create timespan
		if self.getConfigValue('is_pointing_defined'):
			pointing_dates, pointing = self._loadPointingFile(self.getConfigValue('pointing_file'))
			self.pointings[self.getConfigValue('primary_satellite_ids')[0]] = pointing
			if self.getConfigValue('pointing_defines_timespan'):
				console.send(f"Loading timespan from pointing file.")
				self.timespan = timespan.TimeSpan.fromDatetime(pointing_dates)
		else:
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
		console.send(f"\tDuration: {self.timespan.time_period}")
		console.send(f"\tNumber of steps: {len(self.timespan)}")

		# Set up workers for orbit propagation
		worker = threading.Worker(self._propagateOrbits, self.timespan, self.getConfigValue('primary_satellite_ids'))
		worker.signals.result.connect(self._storeOrbitData)
		worker.signals.finished.connect(self._procComplete)
		worker.signals.error.connect(self._displayError)

		satplot.threadpool.start(worker)

	def _procComplete(self):
		self.data_ready.emit()

	def _loadPointingFile(self, p_file):
		pointing_q = np.array(())
		pointing_w = np.genfromtxt(p_file, delimiter=',', usecols=(1), skip_header=1).reshape(-1,1)
		pointing_x = np.genfromtxt(p_file, delimiter=',', usecols=(2), skip_header=1).reshape(-1,1)
		pointing_y = np.genfromtxt(p_file, delimiter=',', usecols=(3), skip_header=1).reshape(-1,1)
		pointing_z = np.genfromtxt(p_file, delimiter=',', usecols=(4), skip_header=1).reshape(-1,1)
		pointing_q = np.hstack((pointing_x,pointing_y,pointing_z,pointing_w))
		pointing_dates = np.genfromtxt(p_file, delimiter=',', usecols=(0),skip_header=1, converters={0:date_parser})

		return pointing_dates, pointing_q

	def _propagateOrbits(self, timespan:timespan.TimeSpan, sat_ids:list[int]):
		updated_list = updater.updateTLEs(sat_ids)
		# if collections.Counter(updated_list) == collections.Counter(self.sat_ids):
		# 		self.finished.emit()
		# 	else:
		# 		self.error.emit

		tle_paths = updater.getTLEFilePaths(sat_ids)
		console.send(f"Propagating orbit from {tle_paths[0].split('/')[-1]} ...")
		orbits = {}
		for ii, sat_id in enumerate(sat_ids):
			orbits[sat_id] = orbit.Orbit.fromTLE(timespan, tle_paths[ii])

				# CONSTELLATION
				# if self.c_config is not None:
				# 	self.c_list = []
				# 	num_c_sats = len(spacetrack.getSatIDs(self.c_config))
				# 	if not use_temp:
				# 		spacetrack.updateTLEs(self.c_config)
				# 	else:
				# 		celestrak.updateTLEs(self.c_config)
				# 	console.send(f"Propagating constellation orbits ...")
				# 	ii = 0
				# 	for sat_id in progressbar(spacetrack.getSatIDs(self.c_config)):
				# 		pc = ii/num_c_sats*100
				# 		bar_str = int(pc)*'='
				# 		space_str = (100-int(pc))*'  '
				# 		console.send(f'Loading {pc:.2f}% ({ii} of {num_c_sats}) |{bar_str}{space_str}|\r')

				# 		if not use_temp:
				# 			c_path = spacetrack.getTLEFilePath(sat_id)

				# 		else:
				# 			c_path = celestrak.getTLEFilePath(sat_id)

				# 		self.c_list.append(orbit.Orbit.fromTLE(self.t, c_path, astrobodies=False))
				# 		ii += 1
				# 	console.send(f"\tLoaded {len(self.c_list)} satellites from the {self.c_config['name']} constellation.")

		return orbits

	def _storeOrbitData(self, orbits):
		self.orbits = orbits

def date_parser(d_bytes):
	d_bytes = d_bytes[:d_bytes.index(b'.')+4]
	s = d_bytes.decode('utf-8')
	d = dt.datetime.strptime(s,"%Y-%m-%d %H:%M:%S.%f")
	d = d.replace(tzinfo=dt.timezone.utc)
	return d.replace(microsecond=0)
