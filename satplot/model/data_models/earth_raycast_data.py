import datetime as dt
import logging
import numpy as np
from numpy import typing as nptyping
import pathlib
from progressbar import progressbar
import pymap3d
from typing import Any
import warnings

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
		# self.data[self._getNextDataIdx()] = sphere_img_data.SphereImageData.visibleEarthEclipsed()


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

	def rayCastFromSensor(self, sens_eci_transform:np.ndarray, sens_rays_cf:np.ndarray, curr_dt:dt.datetime) -> np.ndarray:
		'''[summary]

		[description]

		Args:
			sens_eci_transform (np.ndarray[4,4]): [description]
			sens_rays_cf (np.ndarray[n,4]): [description]
			curr_dt (dt.datetime): [description]

		Returns:
			[type]: [description]
		'''
		num_rays = len(sens_rays_cf)
		cf_norms = np.linalg.norm(sens_rays_cf[:,:3],axis=1)
		sens_rays_eci = sens_eci_transform[:3,:3].dot(sens_rays_cf[:,:3].T).T
		sens_rays_ecf = np.array(pymap3d.eci2ecef(sens_rays_eci[:,0],sens_rays_eci[:,1],sens_rays_eci[:,2],curr_dt)).T
		norms = np.linalg.norm(sens_rays_eci,axis=1)
		pos_eci = sens_eci_transform[:3,3]
		pos_ecf = np.asarray(pymap3d.eci2ecef(pos_eci[0], pos_eci[1], pos_eci[2],curr_dt))
		cart_to_earth, valid = self._lineOfSightToSurface(pos_ecf, sens_rays_ecf)
		lats = np.zeros(num_rays)
		lons = np.zeros(num_rays)
		lats[valid], lons[valid] = self._convertCartesianToEllipsoidGeodetic(cart_to_earth[valid,:])
		data = self.getPixelDataOnSphere(lats, lons)
		rays_shape = sens_rays_cf.shape
		full_img = np.zeros((num_rays, 3))
		full_img[valid] = data[valid]
		return full_img

	def rayCastFromSensor2(self, sens_eci_transform:np.ndarray, sens_rays_cf:np.ndarray, curr_dt:dt.datetime) -> np.ndarray:
		'''[summary]

		[description]

		Args:
			sens_eci_transform (np.ndarray[4,4]): [description]
			sens_rays_cf (np.ndarray[n,4]): [description]
			curr_dt (dt.datetime): [description]

		Returns:
			[type]: [description]
		'''

		cf_norms = np.linalg.norm(sens_rays_cf[:,:3],axis=1)
		# print(f'{cf_norms.max()=}')
		sens_rays_eci = sens_eci_transform[:3,:3].dot(sens_rays_cf[:,:3].T).T
		# sens_rays_ecf = np.array(pymap3d.eci2ecef(sens_rays_eci[:,0],sens_rays_eci[:,1],sens_rays_eci[:,2],curr_dt)).T
		norms = np.linalg.norm(sens_rays_eci,axis=1)
		# print(f'{norms.max()=}')
		# pos_ecf = np.asarray(pymap3d.eci2ecef(sens_eci_transform[3,0],sens_eci_transform[3,1],sens_eci_transform[3,2],curr_dt))
		# cart_to_earth, valid = self._lineOfSightToSurface(pos_ecf, sens_rays_ecf)
		# lats, lons = self._convertCartesianToEllipsoidGeodetic(cart_to_earth)

		return sens_rays_eci
		# return self.getPixelDataOnSphere(lats, lons)

	def _convertCartesianToEllipsoidGeodetic(self, cart:np.ndarray, iters:int=3) -> tuple[np.ndarray, np.ndarray]:
		'''
		Compute latitude and longitude on ellipsoid Earth for an array of cartesian vectors

		Parameters:
			cart_vector (ndarray(dtype=float, ndim = [3,N])): array of ECEF vectors
			iterations (int) (optional): number of iterations to improve calculation accuracy. Default / recommended max = 3.

		Returns:
			lat (ndarray(dtype=float, ndim = N)): latitudes of input points
			lon (ndarray(dtype=float, ndim = N)): longitudes of input pointsq
		'''

		x, y, z = cart.T
		lon = np.degrees(np.arctan2(y,x))
		inverse_flattening = 298.257223563 #wikipedia
		f = 1.0 / inverse_flattening
		_e2 = 2.0*f - f*f
		a = 6371
		e2 = _e2
		R = np.sqrt(x*x + y*y)
		lat = np.arctan2(z, R)
		for ii in range(iters): # 3 iterations for max accuracy
			sin_lat = np.sin(lat)
			e2_sin_lat = e2 * sin_lat
			# At 0°, aC = 6378 km, Earth's actual radius at the equator.
			# At 90°, aC = 6399 km, Earth's radius of curvature at the pole.
			aC = a / np.sqrt(1.0 - e2_sin_lat * sin_lat)
			hyp = z + aC * e2_sin_lat
			lat = np.arctan2(hyp, R)

		lat = np.degrees(lat)
		return lat, lon

	def _lineOfSightToSurface(self, position, rays, target = 'earth'):
		"""
		Find the intersection of rays from position with the WGS-84 geoid, position and rays in ECEF

		Parameters:
			position (ndarray(dtype=float, ndim=3)): ECEF position vector of spacecraft
			pointing (ndarray(dtype=float, ndim=[N,3])): unit vectors defining ECEF pointing directions

		Returns:
			ndarray(dtype=float, ndim=[N,3]): ECEF cartesian vectors describing closest point on earth that each ray intersects
			valid (ndarray(dtype=bool, ndim=N)): boolean array indicating whether a ray intersects the Earth (True), or not
		"""
		pad = 0
		if target == 'atmosphere':
			pad = 50

		num_vectors, dim = rays.shape

		valid = np.ones(num_vectors).astype('bool')

		a = 6378137.0 + (pad * 1000)
		b = 6378137.0 + (pad * 1000)
		c = 6356752.314245 + (pad * 1000)
		x = position[0] * 1000
		y = position[1] * 1000
		z = position[2] * 1000
		u = rays[:,0] * 1000
		v = rays[:,1] * 1000
		w = rays[:,2] * 1000

		# pre-compute to avoid calculating the same thing many times
		a2 = a**2
		b2 = b**2
		c2 = c**2

		x2 = x**2
		y2 = y**2
		z2 = z**2

		u2 = u**2
		v2 = v**2
		w2 = w**2

		value = -a2*b2*w*z - a2*c2*v*y - b2*c2*u*x
		radical = a2*b2*w2 + a2*c2*v2 - a2*v2*z2 + 2*a2*v*w*y*z - a2*w2*y2 + b2*c2*u2 - b2*u2*z2 + 2*b2*u*w*x*z - b2*w2*x2 - c2*u2*y2 + 2*c2*u*v*x*y - c2*v2*x2

		magnitude = a2*b2*w**2 + a2*c2*v2 + b2*c2*u2
		with warnings.catch_warnings(): #ignore errors in computing d, since we deliberately let through invalid values here, to cull them later
			warnings.simplefilter("ignore")
			d = (value - a*b*c*np.sqrt(radical)) / magnitude

		valid[d < 0] = False
		valid[radical < 0] = False

		return np.array([ x + d * u, y + d * v, z + d * w]).T, valid

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		return state

	def deSerialise(self, state):
		super().deSerialise(state)
