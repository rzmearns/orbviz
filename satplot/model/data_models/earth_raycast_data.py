import datetime as dt
import logging
import numpy as np
from numpy import typing as nptyping
import pathlib
from progressbar import progressbar
from typing import Any

import satplot
from satplot.model.data_models.base_models import (BaseDataModel)
import satplot.util.threading as threading
import satplot.model.data_models.data_types as data_types
import satplot.model.data_models.sphere_img_data as sphere_img_data
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class EarthRayCastData(BaseDataModel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type',data_types.DataType.PLANETARYRAYCAST)
		# initialise empty config
		self._setConfig('body_name', 'earth')

		self.lookups: dict[int,dict[str,tuple[float,float]|str|bool]] = {}
		self.data: dict[int, sphere_img_data.SphereImageData] = {}
		self._worker_threads: dict[str, threading.Worker | None] = {}

		self.process()

	# def setPrimaryConfig(self, primary_config:data_types.PrimaryConfig) -> None:
	# 	self.updateConfig('primary_satellite_config', primary_config)
	# 	self.updateConfig('primary_satellite_ids', primary_config.getSatIDs())

	# def setSupplementalConstellation(self, constellation_config:data_types.ConstellationConfig) -> None:
	# 	self.updateConfig('has_supplemental_constellation', True)
	# 	self.constellation = constellation_data.ConstellationData(constellation_config)

	# def clearSupplementalConstellation(self) -> None:
	# 	self.updateConfig('has_supplemental_constellation', False)
	# 	self.constellation = None

	# def getTimespan(self) -> timespan.TimeSpan:
	# 	if self.timespan is None:
	# 		logger.warning(f'History data:{self} does not have a timespan yet')
	# 		raise ValueError(f'History data:{self} does not have a timespan yet')
	# 	return self.timespan

	# def getPrimaryConfig(self) -> data_types.PrimaryConfig:
	# 	return self.getConfigValue('primary_satellite_config')

	# def getPrimaryConfigIds(self) -> list[int]:
	# 	return self.getConfigValue('primary_satellite_ids')

	# def getConstellation(self) -> constellation_data.ConstellationData:
	# 	if self.constellation is None:
	# 		logger.warning(f'History data:{self} does not have a constellation yet')
	# 		raise ValueError(f'History data:{self} does not have a constellation yet')
	# 	else:
	# 		return self.constellation

	# def hasOrbits(self) -> bool:
	# 	if len(self.orbits.values()) > 0:
	# 		return True
	# 	else:
	# 		return False

	# def getOrbits(self) -> dict[int,orbit.Orbit]:
	# 	if len(self.orbits.values()) == 0:
	# 		logger.warning(f'History data:{self} has no orbits yet')
	# 		raise ValueError(f'History data:{self} has no orbits yet')
	# 	return self.orbits

	# def getPointings(self) -> dict[int, nptyping.NDArray[np.float64]]:
	# 	if len(self.pointings.values()) == 0:
	# 		logger.warning(f'History data:{self} has no pointings yet')
	# 		raise ValueError(f'History data:{self} has no pointings yet')
	# 	return self.pointings

	def getPixelDataOnSphere(self, lat:float|np.ndarray, lon:float|np.ndarray,
								min_wavelength:float=400, max_wavelength:float=700) -> np.ndarray:
		# TODO: check lengs of lat and lon are same
		# TODO: handle float option
		shape = lat.shape
		out_arr = np.ndarray((shape[0],3))
		sunlit_mask = self.isLocationSunlit(lat, lon)
		sunlit_data = self.data[self.lookup(min_wavelength, max_wavelength, True)]
		eclipsed_data = self.data[self.lookup(min_wavelength, max_wavelength, True)]
		out_arr[sunlit_mask,:] = sunlit_data.getPixelDataOnSphere(lat[sunlit_mask],lon[sunlit_mask])
		out_arr[~sunlit_mask,:] = eclipsed_data.getPixelDataOnSphere(lat[~sunlit_mask],lon[~sunlit_mask])
		return out_arr

	def lookup(self, min_wavelength:float, max_wavelength:float, lit:bool):
		# TODO: add in other lookup conditions
		lighting_condition_dict = dict(filter(self._filterSunlit, self.lookups.items()))
		if len(lighting_condition_dict.keys()) > 0:
			return list(lighting_condition_dict.keys())[0]
		else:
			raise ValueError(f'There is spherical image data for {self}, matching the conditions: lit=={lit}')

	def _filterSunlit(self, item):
		return item[1]['externally_lit']

	def isLocationSunlit(self, lat:float|np.ndarray, lon:float|np.ndarray) -> np.ndarray:
		# TODO: handle float option
		shape = lat.shape
		# TODO: perform actual sunlit check
		return np.logical_not(np.zeros(shape))

	def _createNewThreadKeyFromIdx(self, idx:int) -> str:
		return f'earth_img_loader_{idx}'

	def _getNextDataIdx(self):
		num = len(self.data.keys())
		return num

	def process(self) -> None:
		# Set up workers for loading default planetary image data
		# Earth visible
		self.data[self._getNextDataIdx()] = sphere_img_data.SphereImageData.visibleEarthSunlit()
		self.data[self._getNextDataIdx()] = sphere_img_data.SphereImageData.visibleEarthEclipsed()


		for idx in self.data.keys():
			thread_name = self._createNewThreadKeyFromIdx(idx)
			self.lookups[idx] = self.data[idx].getLookupData()
			self._worker_threads[thread_name] = threading.Worker(self.data[idx].loadSource)
			self._worker_threads[thread_name].signals.result.connect(self.data[idx].storeArray)
			self._worker_threads[thread_name].signals.finished.connect(self._procComplete)
			self._worker_threads[thread_name].signals.error.connect(self._displayError)
			self._worker_threads[thread_name].setAutoDelete(True)

		for thread_name, thread in self._worker_threads.items():
			if thread is not None:
				logger.info(f'Starting thread {thread_name}:{thread}')
				satplot.threadpool.logStart(thread)

	def _procComplete(self) -> None:
		print(f'inside _procComplete')
		logger.info("Thread completion triggered loading of raycasting image data ")
		for thread in self._worker_threads.values():
			if thread is not None:
				if thread.isRunning():
					logger.info(f"{thread} is still running")
					return
		self.data_ready.emit()
		logger.info("Finished initialising Earth PlanetaryRayCastData")


	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		return state

	def deSerialise(self, state):
		super().deSerialise(state)
