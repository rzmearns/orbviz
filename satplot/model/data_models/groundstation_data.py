import datetime as dt
import json
import logging
import pathlib

from typing import cast

import numpy as np
import pymap3d
from spherapy.orbit import Orbit
from spherapy.timespan import TimeSpan

from satplot.model.data_models.base_models import BaseDataModel
import satplot.util.conversion as satplot_conversions
import satplot.util.hashing as satplot_hashing

logger = logging.getLogger(__name__)

class GroundStationCollection:
	# TODO: use hashes to key instead of names
	def __init__(self):
		self._stations = {}

	def getEnabledDict(self):
		en_list = {}
		for k, gs in self._stations.items():
			en_list[k] = {'file':gs.file,
							'hash':gs.hash}

		return en_list

	def getStations(self):
		return self._stations

	def updateTimespans(self, timespan:TimeSpan):
		for station in self._stations.values():
			station.reloadTimespan(timespan)

	def createGroundStations(self, gs_files:dict[str,pathlib.Path|str]):
		req_hashes= [file['hash'] for file in gs_files]
		to_delete = []
		for station_name, station in self._stations.items():
			if station.hash not in req_hashes:
				to_delete.append(station_name)

		for el in to_delete:
			del self._stations[el]

		for gs_file in gs_files:
			gs = GroundStation(gs_file['file'])
			if gs.name not in self._stations.keys():
				self._stations[gs.name] = gs

class GroundStation(BaseDataModel):
	def __init__(self, gs_file:pathlib.Path):
		super().__init__()
		self._source_timespan = None
		self._source_file = gs_file
		self._source_file_hash = satplot_hashing.md5(gs_file)
		self._loadGSFile(gs_file)

	def _loadGSFile(self, gs_file:pathlib.Path):
		with gs_file.open('r') as fp:
			data = json.load(fp)

		for key in ['name', 'latitude', 'longitude']:
			if key not in data.keys():
				logger.error("Ground station file: %s, missing key '%s'", gs_file, key)
				raise ValueError(f"Ground station file: {gs_file}, missing key '{key}'")

		self._name = data['name']
		self._latlon = (data['latitude'], data['longitude'])


		if 'altitude' in data.keys():
			self._alt = data['altitude']
		else:
			self._alt = 0

		self._ecef = np.asarray(pymap3d.ecef.geodetic2ecef(self._latlon[0], self._latlon[1], self._alt, deg=True))/1000

		if 'uplink' in data.keys():
			self._uplink_config = {'min_freq':data['uplink']['min_frequency'],
									'max_freq':data['uplink']['max_frequency'],
									'min_elev':data['min_elevation'],
									'max_pow':data['uplink']['max_power']}
		else:
			self._uplink_config = None

		if 'downlink' in data.keys():
			self._downlink_config = {'min_freq':data['uplink']['min_frequency'],
									'max_freq':data['uplink']['max_frequency'],
									'min_elev':data['min_elevation'],
									'max_pow':data['uplink']['max_power']}
		else:
			self._downlink_config = None

	def _reloadECIPos(self):
		if self._source_timespan is not None:
			self._eci = np.zeros((len(self._source_timespan), 3))
			for ii in range(len(self._source_timespan)):
				tstamp = self._source_timespan.asDatetime(ii)
				cast("dt.datetime", tstamp)
				self._eci[ii,:] = pymap3d.eci.ecef2eci(self._ecef[0],self._ecef[1],self._ecef[2], tstamp)


	def reloadTimespan(self, new_timespan:TimeSpan):
		if self._source_timespan == new_timespan:
			print('NO NEED TO UPDATE GROUNDSTATION')
			return
		self._source_timespan = new_timespan
		self._reloadECIPos()

	@property
	def name(self):
		return self._name

	@property
	def file(self):
		return self._source_file

	@property
	def hash(self):
		return self._source_file_hash

	@property
	def eci(self):
		return self._eci

	@property
	def ecef(self):
		return self._ecef

	@property
	def latlon(self):
		return self._latlon

	@property
	def alt(self):
		return self._alt

	@property
	def uplink_config(self):
		return self._uplink_config

	@property
	def downlink_config(self):
		return self._downlink_config
