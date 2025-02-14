import numpy as np
import datetime as dt
import sys
import pathlib
import collections

import satplot
from satplot.model.data_models.base import (BaseDataModel)
import satplot.model.data_models.data_types as data_types
import spherapy.orbit as orbit

# constellation_config
# constellation_name
# constellation_beam_angle


class ConstellationData(BaseDataModel):
	def __init__(self, config, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type', data_types.DataType.CONSTELLATION)

		# initialise empty config
		self._setConfig('constellation_name', None)
		self._setConfig('satellite_ids', None) # keys of orbits, position dict
		self._setConfig('beam_angle_deg', None)

		self.updateConfig('constellation_name', config['name'])
		self.updateConfig('beam_angle_deg', config['beam_width'])
		self.updateConfig('satellite_ids', list(config['satellites'].values()))

		self.timespan = None
		self.orbits = {}

	def setTimespan(self, timespan):
		self.timespan = timespan

	def _storeOrbitData(self, orbits:dict[int,orbit.Orbit]) -> None:
		self.orbits = orbits