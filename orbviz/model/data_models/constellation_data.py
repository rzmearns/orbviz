import logging

from typing import Any

import spherapy.orbit as orbit
import spherapy.timespan as timespan

from orbviz.model.data_models.base_models import BaseDataModel
import orbviz.model.data_models.data_types as data_types

# constellation_config
# constellation_name
# constellation_beam_angle

logger = logging.getLogger(__name__)

class ConstellationData(BaseDataModel):
	def __init__(self, config, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type', data_types.DataType.CONSTELLATION)

		# initialise empty config
		self._setConfig('constellation_name', None)
		self._setConfig('satellite_ids', None) # keys of orbits, position dict
		self._setConfig('beam_angle_deg', None)

		self.updateConfig('constellation_name', config.name)
		self.updateConfig('beam_angle_deg', config.beam_width)
		self.updateConfig('satellite_ids', list(config.sats.keys()))

		self.timespan: timespan.TimeSpan | None = None
		self.orbits: dict[int, orbit.Orbit] = {}

	def setTimespan(self, timespan:timespan.TimeSpan) -> None:
		self.timespan = timespan

	def getTimespan(self) -> timespan.TimeSpan:
		if self.timespan is None:
			logger.error('Constellation data:%s does not have a timespan yet', self)
			raise ValueError(f'Constellation data:{self} does not have a timespan yet')
		return self.timespan

	def getOrbits(self) -> dict[int,orbit.Orbit]:
		if len(self.orbits.values()) == 0:
			logger.error('Constellation data:%s has no orbits yet', {self})
			raise ValueError(f'Constellation data:{self} has no orbits yet')
		return self.orbits

	def _storeOrbitData(self, orbits:dict[int,orbit.Orbit]) -> None:
		self.orbits = orbits


	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['orbits'] = self.orbits
		# don't serialise timespan, link it back to history data at deserialisation time
		state['config'] = self.config

		return state

	def deSerialise(self,state):
		self.orbits = state['orbits']
		super().deSerialise(state)

	@classmethod
	def emptyForDeSerialisation(cls):
		return cls({'name':'','beam_width':0,'satellites':{}})