import logging
import numpy as np
import pathlib
from PIL import Image
import sys
from typing import Any

import satplot.model.geometry.spherical as spherical_geom
from satplot.model.data_models.base_models import (BaseDataModel)
import satplot.model.data_models.data_types as data_types
import satplot.util.paths as satplot_paths
import satplot.util.threading as threading

logger = logging.getLogger(__name__)

class SphereImageData(BaseDataModel):
	def __init__(self, source:pathlib.Path, body_name:str, externally_lit:bool, min_wavelength:float=400, max_wavelength:float=700, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setConfig('data_type', data_types.DataType.SPHEREIMAGE)

		# initialise empty config
		self._setConfig('body_name', None)
		self._setConfig('wavelength', (None, None))
		self._setConfig('img_path', None)
		self._setConfig('resolution', (None, None))
		self._setConfig('externally_lit', None)
		self.arr: np.ndarray | None = None

		self.updateConfig('body_name', body_name)
		self.updateConfig('wavelength', (min_wavelength, max_wavelength))
		self.updateConfig('img_path', source)
		self.updateConfig('externally_lit', externally_lit)

		logger.info(f"Finished initialising SphereImageData:{self} for {self.getConfigValue('body_name')}:" \
					f"{self.getConfigValue('wavelength')[0]}nm -> {self.getConfigValue('wavelength')[1]}, "\
					f"externally lit: {self.getConfigValue('externally_lit')}")

	def loadSource(self, running:threading.Flag):
		im = Image.open(pathlib.Path(self.config['img_path']))
		return np.array(im)

	def storeArray(self, arr:np.ndarray) -> None:
		logger.info(f"Finished loading image array data for {self.getConfigValue('body_name')}:" \
					f"{self.getConfigValue('wavelength')[0]}nm -> {self.getConfigValue('wavelength')[1]}, "\
					f"externally lit: {self.getConfigValue('externally_lit')}")
		self.arr = arr
		res = (arr.shape[1],arr.shape[0])
		self.updateConfig('resolution', res)

	def getLookupData(self) -> dict[str,tuple[float,float]|str|bool]:
		d = {'body_name':self.getConfigValue('body_name'),
			'wavelength':self.getConfigValue('wavelength'),
			'externally_lit':self.getConfigValue('externally_lit')}
		return d

	def getPixelDataOnSphere(self, lat:float|np.ndarray, lon:float|np.ndarray) -> np.ndarray:
		if self.arr is None:
			logger.error(f"{self.getConfigValue('body_name')}: SphereImage Data not loaded yet")
			raise ValueError(f"{self.getConfigValue('body_name')}: SphereImage Data not loaded yet")
		if lat.shape[0] == 0:
			return np.ndarray((0,0,3))
		res = self.getConfigValue('resolution')
		lon = spherical_geom.wrapToCircleRangeDegrees(lon)
		lat_pixel_coords = ((90-lat) / 180 * res[1]).astype(int)
		lon_pixel_coords = ((lon+180) / 360 * res[0]).astype(int)
		return self.arr[lat_pixel_coords, lon_pixel_coords,:]

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		return state

	def deSerialise(self,state):
		self.orbits = state['orbits']
		super().deSerialise(state)

	@classmethod
	def visibleEarthSunlit(cls):
		return cls(pathlib.Path(f'{satplot_paths.data_dir}/earth2D/BlueMarble_hires.jpeg'),
					'earth', True)

	@classmethod
	def visibleEarthEclipsed(cls):
		return cls(pathlib.Path(f'{satplot_paths.data_dir}/earth2D/BlackMarble_hires.jpeg'),
					'earth', False)