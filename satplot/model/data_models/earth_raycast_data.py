import datetime as dt
import logging
import numpy as np
from numpy import typing as nptyping
import pathlib
from progressbar import progressbar
import pymap3d
from typing import Any
import warnings

import matplotlib.pyplot as plt

import satplot
from satplot.model.data_models.base_models import (BaseDataModel)
import satplot.util.constants as satplot_const
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

	def getPixelDataOnSphere(self, lat:float|np.ndarray, lon:float|np.ndarray, sunlit_mask:np.ndarray,
								min_wavelength:float=400, max_wavelength:float=700) -> np.ndarray:
		# TODO: check lengs of lat and lon are same
		# TODO: handle float option
		shape = lat.shape
		out_arr = np.ndarray((shape[0],3))
		sunlit_data_src = self.data[self.lookup(min_wavelength, max_wavelength, True)]
		eclipsed_data_src = self.data[self.lookup(min_wavelength, max_wavelength, False)]
		out_arr[sunlit_mask,:] = sunlit_data_src.getPixelDataOnSphere(lat[sunlit_mask],lon[sunlit_mask])
		out_arr[~sunlit_mask,:] = eclipsed_data_src.getPixelDataOnSphere(lat[~sunlit_mask],lon[~sunlit_mask])
		return out_arr

	def lookup(self, min_wavelength:float, max_wavelength:float, lit:bool):
		lighting_condition_dict = {k:v for (k,v) in self.lookups.items() if v['externally_lit'] == lit}
		if len(lighting_condition_dict.keys()) > 0:
			# TODO: add in other lookup conditions
			return list(lighting_condition_dict.keys())[0]
		else:
			raise ValueError(f'There is no spherical image data for {self}, matching the conditions: lit=={lit}')

	def _filterSunlit(self, item):
		# item is a tuple of (dict_id, dict)
		return item[1]['externally_lit']

	def _calcSunlitSurfaceMask(self, cart_earth_intsct:float|np.ndarray, sun_ecf:float|np.ndarray) -> np.ndarray:
		# TODO: handle float option
		unit_carts = cart_earth_intsct/np.linalg.norm(cart_earth_intsct, axis=1).reshape(-1,1)
		unit_sun_ecf = (sun_ecf*1000-cart_earth_intsct)/np.linalg.norm(sun_ecf*1000 - cart_earth_intsct, axis=1).reshape(-1,1)
		dp = np.sum(unit_carts*unit_sun_ecf, axis=1)
		return dp>0

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
		logger.info("Finished loading single raycasting image data")
		for thread in self._worker_threads.values():
			if thread is not None:
				if thread.isRunning():
					logger.info(f"{thread} is still running")
					return
		self.data_ready.emit()
		logger.info("Finished initialising Earth PlanetaryRayCastData")

	def rayCastFromSensor(self, sens_eci_transform:np.ndarray, sens_rays_cf:np.ndarray,
								curr_dt:dt.datetime, sun_eci:np.ndarray,
								draw_eclipse:bool=True,
								draw_atm:bool=False, atm_height:int=150,
								atm_lit_colour:tuple[int,int,int]=(168, 231, 255), atm_eclipsed_colour:tuple[int,int,int]=(23, 32, 35),
								highlight_edge:bool=False, highlight_height:int=10, highlight_colour:tuple[int,int,int]=(255,0,0)) -> np.ndarray:
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

		# convert sensor frame to eci
		sens_rays_eci = sens_eci_transform[:3,:3].dot(sens_rays_cf[:,:3].T).T
		pos_eci = sens_eci_transform[:3,3]

		# convert eci frame to ecef
		sens_rays_ecf = np.array(pymap3d.eci2ecef(sens_rays_eci[:,0],sens_rays_eci[:,1],sens_rays_eci[:,2],curr_dt)).T
		pos_ecf = np.asarray(pymap3d.eci2ecef(pos_eci[0], pos_eci[1], pos_eci[2],curr_dt))
		sun_ecf = np.asarray(pymap3d.eci2ecef(sun_eci[0], sun_eci[1], sun_eci[2],curr_dt))
		# check intersection of rays with earth
		cart_earth_intsct, earth_intsct = self._lineOfSightToSurface(pos_ecf, sens_rays_ecf)
		lats = np.zeros(num_rays)
		lons = np.zeros(num_rays)
		lats[earth_intsct], lons[earth_intsct] = self._convertCartesianToEllipsoidGeodetic(cart_earth_intsct[earth_intsct,:])
		if draw_eclipse:
			surface_sunlit_mask = self._calcSunlitSurfaceMask(cart_earth_intsct, sun_ecf)
		else:
			surface_sunlit_mask = earth_intsct.copy()

		# get earth surface data
		data = self.getPixelDataOnSphere(lats, lons, surface_sunlit_mask)

		# populate img array
		full_img = np.zeros((num_rays, 3))
		full_img[earth_intsct] = data[earth_intsct]

		all_intsct = earth_intsct.copy()

		if draw_atm:

			# atmosphere height (atm_height) function parameter
			Re = satplot_const.R_EARTH
			delta_max = np.pi-np.arcsin(Re/(Re+atm_height))
			cos_delta_max = np.cos(delta_max)

			# check intersection of rays with atmosphere
			cart_atm_intsct, atm_valid = self._lineOfSightToSurface(pos_ecf, sens_rays_ecf, atm_height=atm_height)
			unit_cart_atm_intsct = cart_atm_intsct/np.linalg.norm(cart_atm_intsct,axis=1).reshape(-1,1)
			atm_intsct = atm_valid
			atm_intsct[earth_intsct] = False
			all_intsct = np.logical_or(all_intsct, atm_intsct)

			atm_depth = np.zeros((num_rays,1))
			# earth intersecting rays dot product
			unit_cart_earth_intsct = cart_earth_intsct/np.linalg.norm(cart_earth_intsct,axis=1).reshape(-1,1)
			v = cart_earth_intsct[earth_intsct]-(pos_ecf*1000)
			unit_v = v/np.linalg.norm(v,axis=1).reshape(-1,1)
			dp = np.sum(unit_cart_earth_intsct[earth_intsct]*unit_v,axis=1).reshape(-1,1)

			# atmospheric depth along ray for those rays intersecting earth
			atm_depth[earth_intsct] = np.sqrt((Re+atm_height)**2 + Re**2*(dp**2-1)) + Re*dp

			# atm intersecting only dot product
			v = cart_atm_intsct[atm_valid] - (pos_ecf*1000)
			unit_v = v/np.linalg.norm(v, axis=1).reshape(-1,1)
			dp = np.sum(unit_cart_atm_intsct[atm_valid]*unit_v,axis=1).reshape(-1,1)

			# atmospheric depth along ray for those rays intersecting atm (but not earth)
			atm_depth[atm_intsct] = 2*(Re+atm_height)*(-1)*dp
			max_alpha = 0.75
			max_atm_depth = 1390.6
			alpha = atm_depth/max_atm_depth * max_alpha

			atm_data = np.zeros((all_intsct.shape[0],3))
			atm_lit_mask = np.zeros(all_intsct.shape, dtype=bool)
			if draw_eclipse:
				unit_sun_ecf = sun_ecf/np.linalg.norm(sun_ecf)
				dp = np.sum(unit_cart_atm_intsct[all_intsct]*unit_sun_ecf, axis=1)
				atm_lit_mask[all_intsct] = dp > cos_delta_max
				atm_data[atm_lit_mask] = atm_lit_colour
				atm_data[np.logical_and(~atm_lit_mask, all_intsct)] = atm_eclipsed_colour
			else:
				atm_lit_mask[all_intsct] = True
				atm_data[atm_lit_mask] = atm_lit_colour
				atm_data[np.logical_and(~atm_lit_mask, all_intsct)] = atm_eclipsed_colour

			temp_data = alpha[all_intsct]*atm_data[all_intsct] + (1-alpha[all_intsct])*full_img[all_intsct]
			temp_data = np.clip(temp_data,0,255)
			full_img[all_intsct] = temp_data

		if highlight_edge:
			if draw_atm:
				hh = atm_height + highlight_height
			else:
				hh = highlight_height
			cart_hl_intsct, hl_valid = self._lineOfSightToSurface(pos_ecf, sens_rays_ecf[~all_intsct], atm_height=hh)
			hl_intsct = np.zeros(num_rays, dtype=bool)
			hl_intsct[~all_intsct] = hl_valid
			full_img[hl_intsct] = highlight_colour

		return full_img.astype(np.float32)

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

	def _lineOfSightToSurface(self, position, rays, atm_height=0):
		"""
		Find the intersection of rays from position with the WGS-84 geoid, position and rays in ECEF

		Parameters:
			position (ndarray(dtype=float, ndim=3)): ECEF position vector of spacecraft
			pointing (ndarray(dtype=float, ndim=[N,3])): unit vectors defining ECEF pointing directions

		Returns:
			ndarray(dtype=float, ndim=[N,3]): ECEF cartesian vectors describing closest point on earth that each ray intersects
			valid (ndarray(dtype=bool, ndim=N)): boolean array indicating whether a ray intersects the Earth (True), or not
		"""
		pad = atm_height

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
