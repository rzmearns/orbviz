import logging

import numpy as np
from scipy.spatial import ConvexHull

import orbviz
from orbviz.model.data_models import data_types
import orbviz.model.geometry.polygons as polygons
import orbviz.model.lens_models.pinhole as pinhole

logger = logging.getLogger(__name__)

class SensorData:
	def __init__(self, parent_data_model,
						sc_config:data_types.SpacecraftConfig,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]]):

		self._parent_data_model = parent_data_model
		self._sc_config = sc_config
		self._timestamps = timestamps
		self.earth_raycast_data = orbviz.earth_raycast_data
		num_samples = len(self._timestamps)
		# caches
		# caches are indexed using the timespan index
		self._sens_boundary_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._sens_pixel_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._sens_latlon_cache:dict[tuple[str,str], dict[int,np.ndarray[int,int], np.dtype[np.float64]]] = {}
		self._cached_timesteps:dict[tuple[str,str], np.ndarray[tuple[int],np.dtype[np.bool_]]] = {}

		self._lowres = {}
		self._lowres_rays_sf = {}
		self._lens_model = {}

		for suite_name, suite_config in sc_config.getSensorSuites().items():
			for sens_name in suite_config.getSensorNames():
				sens_key = (suite_name, sens_name)
				# TODO: these should be held in the config class
				self._lowres[sens_key] = self._calcLowRes(suite_config.getSensorConfig(sens_name)['resolution'])
				self._lens_model[sens_key] = pinhole
				self._lowres_rays_sf[sens_key] = self._lens_model[sens_key].generatePixelRays(self._lowres[sens_key],
																								suite_config.getSensorConfig(sens_name)['fov'])

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
			# data already cached, fetch
			return (self._sens_latlon_cache[sens_key][cache_key],
					self._sens_pixel_cache[sens_key][cache_key],
					self._sens_boundary_cache[sens_key][cache_key])

		else:
			# calculate
			all_lats, all_lons = self.earth_raycast_data.rayCastFromSensorFor2D(self._lowres[sens_key],
															self._parent_data_model.getSensorTransform(self._sc_config.id,
																										suite_name,
																										sens_name,
																										timestep_idx),
															self._lowres_rays_sf[sens_key],
															self._timestamps[timestep_idx],
															intersect_only=False)
			lat_lons = np.hstack((all_lats.reshape(-1,1),all_lons.reshape(-1,1)))
			pc, patch1_verts, patch2_verts, split = self._calcPatchBoundaries(all_lats, all_lons)

			self._sens_latlon_cache[sens_key][cache_key] = lat_lons
			self._sens_pixel_cache[sens_key][cache_key] = pc
			self._sens_boundary_cache[sens_key][cache_key] = [patch1_verts, patch2_verts]
			self._cached_timesteps[sens_key][cache_key] = True

			return lat_lons, pc, [patch1_verts, patch2_verts]

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


	def exportDataAsGEOJSONFeatures(self) -> list[dict]:
		feature_list = []
		for jj, sens_key in enumerate(self._sens_boundary_cache.keys()):
			for ii in range(len(self._timestamps)):
				data = self._storeBoundaryAsGEOJSONFeature(self._sc_config.id,
																		jj+1,
																		sens_key[0],
																		sens_key[1],
																		ii)
				if data is not None:
					feature_list.append(data)
		return feature_list

	def _storeBoundaryAsGEOJSONFeature(self, sc_id, unique_sens_id:int, suite_name, sens_name, timestep_idx):
		sens_key = (suite_name, sens_name)
		# print(f'{self._sens_boundary_cache.keys()}')
		# if timestep_idx not in self._sens_boundary_cache[sens_key].keys():
		# 	logger.warning('Exporting GEO JSON data. Sensor: %s does not have data for timestep: %s',sens_key, timestep_idx)
		# 	return None

		d = {}
		d['type'] = "Feature"
		d['properties'] = {}
		d['properties']['ID'] = unique_sens_id
		d['properties']['sat_id'] = sc_id
		d['properties']['sensor_suite'] = suite_name
		d['properties']['sensor_name'] = sens_name
		d['properties']['DateTime'] = self._timestamps[timestep_idx]
		d['geometry'] = {}

		lat_lons, pc, [patch1_verts, patch2_verts] = self.get2DData(suite_name, sens_name, timestep_idx)

		split = True
		if len(patch1_verts) == len(patch2_verts):
			if np.allclose(patch1_verts, patch2_verts):
				split = False

		if (len(patch1_verts)==0) and (len(patch2_verts)==0):
			return {}
		else:
			if split:
				d['geometry']['type'] = 'MultiPolygon'
				out_verts = [polygons.closePolygon(el) for el in [patch1_verts, patch2_verts] if len(el) > 3]
			else:
				d['geometry']['type'] = 'Polygon'
				out_verts = polygons.closePolygon(patch1_verts)

		d['geometry']['coordinates'] = [out_verts]

		return d

	def _calcLowRes(self, true_resolution:tuple[int,int]) -> tuple[int,int]:
		lowres = [0,0]
		max_1D_resolution = 120
		aspect_ratio = true_resolution[0]/true_resolution[1]
		if aspect_ratio > 1:
			lowres = (max_1D_resolution, int(max_1D_resolution/aspect_ratio))
		elif aspect_ratio < 1:
			lowres = (int(max_1D_resolution/aspect_ratio), max_1D_resolution)
		else:
			lowres = (max_1D_resolution, max_1D_resolution)
		return lowres

	def _calcPatchBoundaries(self, lats, lons):
		intsct_lats = lats[~np.isnan(lats)]
		intsct_lons = lons[~np.isnan(lons)]
		point_cloud = np.hstack((intsct_lons.reshape(-1,1),intsct_lats.reshape(-1,1)))
		if len(point_cloud)<3:
			# no sensor polygon
			return point_cloud, np.zeros((0,2), dtype=np.float64), np.zeros((0,2), dtype=np.float64), False
		else:
			if (point_cloud[:,0].max()-point_cloud[:,0].min())>180:
				# point cloud is split across 180 line
				side1_points = point_cloud[np.where(point_cloud[:,0]>0)]
				side2_points = point_cloud[np.where(point_cloud[:,0]<0)]


				# shift points so are straddling 180, rather than wrapping to -180
				shifted_point_cloud = point_cloud.copy()
				shifted_point_cloud[np.where(shifted_point_cloud[:,0]<0)[0],0] += 360
				# find points of polygon which lie on lon 180 line
				ch_all = ConvexHull(shifted_point_cloud)
				shifted_boundary = shifted_point_cloud[ch_all.vertices]
				int_points = polygons.getPolygonVerticalIntersection(shifted_boundary, 180)
				neg_int_points = int_points.copy()
				neg_int_points[:,0] *= -1
				# augment point clouds with intersection points
				side1_points = np.append(side1_points, int_points, axis=0)
				side2_points = np.append(side2_points, neg_int_points, axis=0)


				if len(side1_points) > 2:
					ch1 = ConvexHull(side1_points)
					side1_verts = side1_points[ch1.vertices]
				else:
					# not enough points to draw polygon on eastern hemisphere
					side1_verts = None
				if len(side2_points) > 2:
					ch2 = ConvexHull(side2_points)
					side2_verts = side2_points[ch2.vertices]
				else:
					# not enough points to draw polygon on western hemisphere
					side2_verts = None

				if side2_verts is None:
					return side1_verts, side1_verts, False
				if side1_verts is None:
					return side2_verts, side2_verts, False

				return point_cloud, side1_verts, side2_verts, True

			else:
				# doesn't straddle 180 line
				ch = ConvexHull(point_cloud)
				verts = point_cloud[ch.vertices]

				return point_cloud, verts, verts, False