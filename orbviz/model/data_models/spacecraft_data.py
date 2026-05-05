import logging

import numpy as np

from orbviz.model.data_models import data_types
import orbviz.model.geometry.polygons as polygons
import orbviz.model.geometry.spherical as spherical_geom
import orbviz.util.constants as c

logger = logging.getLogger(__name__)

class SpacecraftData:
	def __init__(self, parent_data_model,
						sc_config:data_types.SpacecraftConfig,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]]):

		self._parent_data_model = parent_data_model
		self._sc_config = sc_config
		self._sc_id = self._sc_config.id
		self._timestamps = timestamps
		num_samples = len(self._timestamps)
		# caches
		# caches are indexed using the timespan index
		self._oth_boundary_cache:dict[int,np.ndarray[tuple[int,int], np.dtype[np.float64]]] = {}
		self._cached_timesteps = np.full((num_samples),False)

	def getTimestamps(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._timestamps

	def get2DData(self, timestep_idx:int):
		cache_key = timestep_idx
		if self._cached_timesteps[cache_key]:
			# data already cached, fetch
			return self._oth_boundary_cache[cache_key]

		else:
			# calculate
			eci_pos = self._parent_data_model.getOrbit(self._sc_id).pos[timestep_idx]
			geo_pos = (self._parent_data_model.getOrbit(self._sc_id).lon[timestep_idx],
						self._parent_data_model.getOrbit(self._sc_id).lat[timestep_idx])
			patch1_verts, patch2_verts = self._calcOTHCircle(eci_pos, geo_pos, timestep_idx)

			self._oth_boundary_cache[cache_key] = [patch1_verts, patch2_verts]
			self._cached_timesteps[cache_key] = True

			return [patch1_verts, patch2_verts]

	def exportDataAsGEOJSONFeatures(self) -> list[dict]:
		feature_list = []
		for ii in range(len(self._timestamps)):
			data = self._storeBoundaryAsGEOJSONFeature(self._sc_config.id, ii)
			if data is not None:
				feature_list.append(data)
		return feature_list

	def _storeBoundaryAsGEOJSONFeature(self, sc_id, timestep_idx):
		d = {}
		d['type'] = "Feature"
		d['properties'] = {}
		d['properties']['ID'] = 1
		d['properties']['sat_id'] = sc_id
		d['properties']['DateTime'] = self._timestamps[timestep_idx]
		d['geometry'] = {}

		[patch1_verts, patch2_verts] = self.get2DData(timestep_idx)

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

	def _calcOTHCircle(self, eci_pos, ecf_pos, curr_idx):
		alt = np.linalg.norm(eci_pos)
		phi = np.rad2deg(np.arccos(c.R_EARTH/(alt)))
		lats, lons1, lons2 = spherical_geom.genSmallCircleCenterSubtendedAngle(phi*2, ecf_pos[1], ecf_pos[0])
		patch1, patch2 = spherical_geom.splitOTHPatch(ecf_pos[0], ecf_pos[1], lats, lons1, lons2)

		return patch1, patch2