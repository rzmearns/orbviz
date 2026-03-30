import logging

import numpy as np
from scipy.ndimage import binary_erosion

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
				if suite_config.getSensorConfig(sens_name)['shape'] == data_types.SensorTypes('square_pyramid'):
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
			pc, patch1_verts, patch2_verts, split = self._calcPatchBoundaries(all_lats, all_lons, self._lowres[sens_key])

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
			return None
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
		# max_1D_resolution = 120
		lowres_ratio = 10
		aspect_ratio = true_resolution[0]/true_resolution[1]
		if aspect_ratio > 1:
			lowres_h = int(true_resolution[1]/lowres_ratio)
			lowres_h = max(3, lowres_h)
			if lowres_h == 3:
				lowres_ratio = true_resolution[1]/lowres_h
			lowres_w = int(true_resolution[0]/lowres_ratio)
		elif aspect_ratio < 1:
			lowres_w = int(true_resolution[0]/lowres_ratio)
			lowres_w = max(3, lowres_w)
			if lowres_w == 3:
				lowres_ratio = true_resolution[0]/lowres_w
			lowres_h = int(true_resolution[1]/lowres_ratio)
		else:
			lowres_w = max(3, int(true_resolution[0]/lowres_ratio))
			lowres_h = max(3, int(true_resolution[1]/lowres_ratio))

		return (lowres_w, lowres_h)

	def _calcPatchBoundaries(self, lats, lons, res):
		intsct_lats = lats[~np.isnan(lats)]
		intsct_lons = lons[~np.isnan(lons)]

		point_cloud = np.hstack((intsct_lons.reshape(-1,1),intsct_lats.reshape(-1,1)))

		if len(point_cloud)<3:
			# no sensor polygon
			return point_cloud, np.zeros((0,2), dtype=np.float64), np.zeros((0,2), dtype=np.float64), False
		else:
			mask = np.invert(np.isnan(lats)).astype(int)
			edge_mask = mask.reshape([res[1], res[0]])
			edge_mask = edge_mask - binary_erosion(edge_mask)
			# Create a boolean mask for all of the pixels between Earth + Space
			edge_mask = edge_mask.astype('bool')

			verts = np.asarray(np.where(edge_mask)).T
			hull_verts = polygons.getAugmentedConvexHullBoundary(verts)
			lats_sq = lats.reshape(res[1],res[0])
			lons_sq = lons.reshape(res[1],res[0])
			edge_lats = lats_sq[hull_verts[:,0], hull_verts[:,1]]
			edge_lons = lons_sq[hull_verts[:,0], hull_verts[:,1]]

			boundary_points = np.vstack((edge_lons, edge_lats)).T

			if (boundary_points[:,0].max()-boundary_points[:,0].min())>180:
				# point cloud is split across 180 line
				side1_points = boundary_points[np.where(boundary_points[:,0]>0)]
				side2_points = boundary_points[np.where(boundary_points[:,0]<0)]

				# shift points so are straddling 180, rather than wrapping to -180
				shifted_boundary_points = boundary_points.copy()
				shifted_boundary_points[np.where(shifted_boundary_points[:,0]<0)[0],0] += 360
				int_points = polygons.getPolygonVerticalIntersection(shifted_boundary_points, 180)
				neg_int_points = int_points.copy()
				neg_int_points[:,0] *= -1
				# augment point clouds with intersection points
				side1_points = np.append(side1_points, int_points, axis=0)
				side2_points = np.append(side2_points, neg_int_points, axis=0)

				if len(side1_points) > 2:
					side1_verts = polygons.reorderCW(side1_points)

				else:
					# not enough points to draw polygon on eastern hemisphere
					side1_verts = None
				if len(side2_points) > 2:
					side2_verts = polygons.reorderCW(side2_points)
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

				return point_cloud, boundary_points, boundary_points, False


