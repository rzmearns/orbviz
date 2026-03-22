import logging

import numpy as np

import orbviz.model.data_models.data_types as data_types
import orbviz.model.geometry.polygons as polygons

logger = logging.getLogger(__name__)

class SensorData:
	def __init__(self, sc_config:data_types.SpacecraftConfig,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]]):

		self._sc_config = sc_config
		self._timestamps = timestamps
		num_samples = len(self._timestamps)
		# caches
		# caches are indexed using the timespan index
		self._sens_boundary_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._sens_pixel_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._sens_latlon_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._cached_timesteps:dict[tuple[str,str], np.ndarray[tuple[int],np.dtype[np.bool_]]] = {}

		for suite_name, suite_config in sc_config.getSensorSuites().items():
			for sens_name in suite_config.getSensorNames():
				sens_key = (suite_name, sens_name)
				self._sens_boundary_cache[sens_key] = {}
				self._sens_pixel_cache[sens_key] = {}
				self._sens_latlon_cache[sens_key] = {}
				self._cached_timesteps[sens_key] = np.full((num_samples),False)

	def getTimestamps(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._timestamps

	# def _getCache(self, suite_name:str, sens_name:str, cache_dict):
	# 	sens_key = (suite_name, sens_name)
	# 	if sens_key not in cache_dict.keys():
	# 		cache_dict[sens_key] = {}

	# 	return cache_dict[sens_key]

	# def getSensor2DBoundary(self, suite_name:str, sens_name:str, timestep_idx:int):
	# 	sens_key = (suite_name, sens_name)
	# 	cache_key = timestep_idx
	# 	if self._cached_timesteps[sens_key][cache_key]:
	# 		return self._sens_boundary_cache[cache_key]
	# 	else:
	# 		return None

	def get2DData(self, suite_name:str, sens_name:str, timestep_idx:int):
		sens_key = (suite_name, sens_name)
		cache_key = timestep_idx
		if self._cached_timesteps[sens_key][cache_key]:
			return (self._sens_latlon_cache[sens_key][cache_key],
					self._sens_pixel_cache[sens_key][cache_key],
					self._sens_boundary_cache[sens_key][cache_key])

		else:
			return None, None, None

	def submit2DData(self, suite_name:str, sens_name:str, timestep_idx:int,
						latlon_data,
						pixel_locations,
						pixel_boundary_locations):

		sens_key = (suite_name, sens_name)
		cache_key = timestep_idx
		self._sens_latlon_cache[sens_key][cache_key] = latlon_data
		self._sens_pixel_cache[sens_key][cache_key] = pixel_locations
		self._sens_boundary_cache[sens_key][cache_key] = pixel_boundary_locations
		self._cached_timesteps[sens_key][cache_key] = True


	def exportDataAsGEOJSON(self) -> dict:
		d = {}
		d['type'] = 'FeatureCollection'
		d['features'] = []
		for jj, sens_key in enumerate(self._sens_boundary_cache.keys()):
			for ii in range(len(self._timestamps)):
				data = self._storeBoundaryAsGEOJSONFeature(self._sc_config.id,
																		jj+1,
																		sens_key[0],
																		sens_key[1],
																		ii)
				if data is not None:
					d['features'].append(data)
		return d

	def _storeBoundaryAsGEOJSONFeature(self, sc_id, unique_sens_id:int, suite_name, sens_name, timestep_idx):
		sens_key = (suite_name, sens_name)
		# print(f'{self._sens_boundary_cache.keys()}')
		if timestep_idx not in self._sens_boundary_cache[sens_key].keys():
			logger.warning('Exporting GEO JSON data. Sensor: %s does not have data for timestep: %s',sens_key, timestep_idx)
			return None

		d = {}
		d['type'] = "Feature"
		d['properties'] = {}
		d['properties']['ID'] = unique_sens_id
		d['properties']['sat_id'] = sc_id
		d['properties']['sensor_suite'] = suite_name
		d['properties']['sensor_name'] = sens_name
		d['properties']['DateTime'] = self._timestamps[timestep_idx]
		d['geometry'] = {}
		sens_key = (suite_name, sens_name)
		verts = self._sens_boundary_cache[sens_key][timestep_idx]

		if len(verts) == 0:
			return {}
		else:
			if isinstance(verts, list):
				d['geometry']['type'] = 'MultiPolygon'
				out_verts = [polygons.closePolygon(el) for el in verts]
			else:
				d['geometry']['type'] = 'Polygon'
				out_verts = polygons.closePolygon(verts)

		d['geometry']['coordinates'] = [out_verts]

		return d
