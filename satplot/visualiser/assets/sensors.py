import datetime as dt
import logging
import numpy as np
import numpy.typing as nptyping
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
import time
from typing import Any

import vispy.scene.visuals as vVisuals
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.filters as vFilters
import vispy.visuals.transforms as vTransforms
from vispy.util.quaternion import Quaternion

import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.geometry.polygons as polygeom
import satplot.model.geometry.spherical as sphericalgeom
import satplot.model.data_models.data_types as satplot_data_types
import satplot.model.lens_models.pinhole as pinhole
import satplot.util.constants as c
import satplot.util.conversion as satplot_conversion
import satplot.visualiser.colours as colours
import satplot.visualiser.assets.base_assets as base_assets

logger = logging.getLogger(__name__)

class SensorSuite3DAsset(base_assets.AbstractCompoundAsset):
	def __init__(self, sens_suite_dict:dict[str,Any], name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		
		self._setDefaultOptions()
		self._initData(sens_suite_dict)
		self._instantiateAssets()
		self._createVisuals()	

		self._attachToParentView()

	def _initData(self, sens_suite_dict:dict[str,Any]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'SensorSuite'
		self.data['sens_suite_config'] = sens_suite_dict

	def setSource(self, *args, **kwargs) -> None:
		pass

	def _instantiateAssets(self) -> None:
		sensor_names = self.data['sens_suite_config'].getSensorNames()
		for sensor in sensor_names:
			logger.info(f"Instantiating 3D sensor asset {self.data['name']}:{sensor}")
			sens_dict = self.data['sens_suite_config'].getSensorConfig(sensor)
			if sens_dict['shape'] == satplot_data_types.SensorTypes.CONE:
				self.assets[sensor] = Sensor3DAsset.cone(sensor, sens_dict, parent=self.data['v_parent'])
			elif sens_dict['shape'] == satplot_data_types.SensorTypes.FPA:
				self.assets[sensor] = Sensor3DAsset.squarePyramid(sensor, sens_dict, parent=self.data['v_parent'])
		self._addIndividualSensorPlotOptions()

	def _createVisuals(self) -> None:
		pass

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		if self.isStale():
			if rotation is None and quat is None:
				logger.warning(f"Rotation and quaternion passed to sensor suite: {self.data['name']} cannot both be None")
				raise ValueError(f"Rotation and quaternion passed sensor suite: {self.data['name']} cannot both be None")
			if rotation is not None and quat is not None:
				logger.warning(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")
				raise ValueError(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")

			for asset in self.assets.values():
				asset.setTransform(pos=pos, rotation=rotation, quat=quat)
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()

	def _addIndividualSensorPlotOptions(self) -> None:
		logger.debug(f'Adding sensor options dictionary entries for:')
		for sens_key in self.assets.keys():
			visibilityCallback = self._makeVisibilityCallback(sens_key)
			self.opts[f'plot_{sens_key}'] = {'value': True,
													'type': 'boolean',
													'help': '',
													'static': False,
													'callback': visibilityCallback,
													'widget_data': None}

	def _makeVisibilityCallback(self, sens_key:str):
		def _visibilityCallback(state):
			self.opts[f'plot_{sens_key}']['value'] = state
			self.assets[f'{sens_key}'].setSensorVisibility(state)
		return _visibilityCallback

	def setSuiteVisibility(self, state:bool) -> None:
		self.setVisibilityRecursive(state)

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True
		for asset in self.assets.values():
			asset.removePlotOptions()

class Sensor3DAsset(base_assets.AbstractSimpleAsset):
	def __init__(self, sensor_name, mesh_verts, mesh_faces,
			  			bf_quat, colour, sens_type=None, v_parent=None, *args, **kwargs):
		super().__init__(sensor_name, v_parent)

		self._setDefaultOptions()
		if sens_type is None or not satplot_data_types.SensorTypes.hasValue(sens_type):
			logger.error(f"Sensor {sensor_name} has an ill-defined sensor type: {sens_type}")
			return ValueError(f"Sensor {sensor_name} has an ill-defined sensor type: {sens_type}")
		self._initData(sens_type, sensor_name, mesh_verts, mesh_faces, bf_quat, colour)

		if self.data['type'] is None:
			logger.error('Sensor() should not be called directly, use one of the constructor methods')
			raise ValueError('Sensor() should not be called directly, use one of the constructor methods')

		self._createVisuals()

		self.setTransform()

		self._attachToParentView()
		print(f"init: {self}")
		
	def _initData(self, sens_type:str, sensor_name:str, mesh_verts:nptyping.NDArray, mesh_faces:nptyping.NDArray, bf_quat:nptyping.NDArray, colour:tuple[float,float,float]):
		self.data['type'] = sens_type
		self.data['name'] = sensor_name
		self.data['mesh_vertices'] = mesh_verts
		self.data['mesh_faces'] = mesh_faces
		self.data['bf_quat'] = bf_quat
		self.data['vispy_quat'] = self.data['bf_quat']
		self.opts['sensor_cone_colour']['value'] = colour

	def setSource(self, *args, **kwargs) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['sensor_cone'] = vVisuals.Mesh(self.data['mesh_vertices'],
    											self.data['mesh_faces'],
    											color=colours.normaliseColour(self.opts['sensor_cone_colour']['value']),
    											parent=None)
		self.setTransform(rotation=Rotation.from_quat(self.data['bf_quat']).as_matrix().reshape(3,3))
		wireframe_filter = vFilters.WireframeFilter(width=1)
		alpha_filter = vFilters.Alpha(self.opts['sensor_cone_alpha']['value'])
		self.visuals['sensor_cone'].attach(alpha_filter)
		self.visuals['sensor_cone'].attach(wireframe_filter)

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		print(f"Call setTransform of:{self}")
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			T = np.eye(4)
			sc_rotation = rotation
			if quat is not None:
				rotation = Rotation.from_quat(quat) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			elif rotation is not None:
				# bf_quat -> bodyframe to cam quaternion
				rotation = Rotation.from_matrix(rotation) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			else:
				rot_mat = np.eye(3)
				as_quat = (1,0,0,0)
			self.data['vispy_quat'] = as_quat
			T[0:3,0:3] = rot_mat
			T[0:3,3] = np.asarray(pos).reshape(-1,3)
			self.visuals['sensor_cone'].transform = vTransforms.linear.MatrixTransform(T.T)
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['sensor_cone_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSensorConeColour,
												'widget_data': None}
		self._dflt_opts['sensor_cone_alpha'] = {'value': 0.5,
										  		'type': 'float',
												'help': '',
												'static': True,
												'callback': self.setSensorConeAlpha,
												'widget_data': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setSensorConeColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['sensor_cone_colour']['value'] = new_colour
		self.visuals['sensor_cone'].set_data(color=colours.normaliseColour(new_colour))

	def setSensorConeAlpha(self, alpha:float) -> None:
		raise NotImplementedError

	def setSensorVisibility(self, state):
		for visual_name, visual in self.visuals.items():
			visual.visible = state

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True

	@classmethod
	def cone(cls, sensor_name:str, sensor_dict:dict[str,Any], parent:ViewBox|None=None):
		mesh_verts, mesh_faces  = polyhedra.calcConeMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['fov'])
		
		bf_quat = np.asarray(sensor_dict['bf_quat']).reshape(1,4)
		colour = sensor_dict['colour']
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='cone', v_parent=parent)

	@classmethod
	def squarePyramid(cls, sensor_name:str, sensor_dict:dict[str,Any], parent:ViewBox|None=None):
		mesh_verts, mesh_faces  = polyhedra.calcSquarePyramidMesh((0,0,0),
								  		sensor_dict['range'],
										(0,0,1),
										sensor_dict['fov'][1],
										sensor_dict['fov'][0],
										axis_sample=2)
		
		bf_quat = np.asarray(sensor_dict['bf_quat']).reshape(1,4)
		colour = sensor_dict['colour']
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='square_pyramid', v_parent=parent)

class SensorSuite2DAsset(base_assets.AbstractCompoundAsset):
	def __init__(self, sens_suite_dict:dict[str,Any], name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData(sens_suite_dict)
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self, sens_suite_dict:dict[str,Any]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'SensorSuite'
		self.data['sens_suite_config'] = sens_suite_dict
		self.data['curr_datetime'] = None
		self.data['horiz_pixel_scale'] = None
		self.data['vert_pixel_scale'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		for sensor_name, sensor in self.assets.items():
			sensor.setSource(args[0])

	def setScale(self, horizontal_size, vertical_size):
		self.data['horiz_pixel_scale'] = horizontal_size/360
		self.data['vert_pixel_scale'] = vertical_size/180
		for asset in self.assets.values():
			asset.setScale(horizontal_size, vertical_size)

	def setCurrentDatetime(self, curr_dt:dt.datetime) -> None:
		self.data['curr_datetime'] = curr_dt
		for asset in self.assets.values():
			asset.setCurrentDatetime(curr_dt)

	def _instantiateAssets(self) -> None:
		sensor_names = self.data['sens_suite_config'].getSensorNames()
		full_sensor_names = [f"{self.data['name']}: {sens_name}" for sens_name in sensor_names]
		for ii, sensor_name in enumerate(sensor_names):
			logger.info(f"Instantiating 2D sensor asset {self.data['name']}:{sensor_name}")
			sens_dict = self.data['sens_suite_config'].getSensorConfig(sensor_name)
			if sens_dict['shape'] == satplot_data_types.SensorTypes.CONE:
				# TOOD: some kind of exception
				pass
			elif sens_dict['shape'] == satplot_data_types.SensorTypes.FPA:
				self.assets[sensor_name] = Sensor2DAsset(full_sensor_names[ii], sens_dict, v_parent=self.data['v_parent'])
		self._addIndividualSensorPlotOptions()

	def _createVisuals(self) -> None:
		pass

	def getSensorByKey(self, sens_key:str):
		return self.assets[sens_key]

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		start = time.monotonic()
		if self.isStale():
			if rotation is None and quat is None:
				logger.warning(f"Rotation and quaternion passed to sensor suite: {self.data['name']} cannot both be None")
				raise ValueError(f"Rotation and quaternion passed sensor suite: {self.data['name']} cannot both be None")
			if rotation is not None and quat is not None:
				logger.warning(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")
				raise ValueError(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")

			for asset in self.assets.values():
				asset.setTransform(pos=pos, rotation=rotation, quat=quat)
			self._clearStaleFlag()
		end = time.monotonic()
		print(f'{end-start=}')

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()

	def _addIndividualSensorPlotOptions(self) -> None:
		logger.debug(f'Adding sensor options dictionary entries for:')
		for sens_key in self.assets.keys():
			visibilityCallback = self._makeVisibilityCallback(sens_key)
			self.opts[f'plot_{sens_key}'] = {'value': True,
													'type': 'boolean',
													'help': '',
													'static': False,
													'callback': visibilityCallback,
													'widget_data': None}

	def _makeVisibilityCallback(self, sens_key:str):
		def _visibilityCallback(state):
			self.opts[f'plot_{sens_key}']['value'] = state
			self.assets[f'{sens_key}'].setSensorVisibility(state)
		return _visibilityCallback

	def setSuiteVisibility(self, state:bool) -> None:
		self.setVisibilityRecursive(state)

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True
		for asset in self.assets.values():
			asset.removePlotOptions()

class Sensor2DAsset(base_assets.AbstractSimpleAsset):
	def __init__(self, name:str|None=None, config:dict={}, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self.config = config
		self._setDefaultOptions()
		self._initData(config['bf_quat'], config['resolution'], config['fov'], config['colour'])
		self._instantiateAssets()
		self._createVisuals()
		self.counter = 0
		self._attachToParentView()
		print(f"init: {self}")

	def _initData(self, bf_quat:tuple[float, float, float, float], resolution:tuple[int,int], fov:tuple[float,float], colour:tuple[int, int, int]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Sensor'
		self.data['bf_quat'] = bf_quat
		self.data['res'] = resolution
		self.data['lowres'] = self._calcLowRes(self.data['res'])
		self.data['fov'] = fov
		self.data['lens_model'] = pinhole
		# rays from each pixel in sensor frame
		self.data['lowres_rays_sf'] = self.data['lens_model'].generatePixelRays(self.data['lowres'], self.data['fov'])
		# need to create a valid polygon for instantiation (but before valid data exists)
		self.data['point_cloud'] = np.zeros((364,2))
		self.data['point_cloud'][:363,0] = np.arange(0,363)
		self.data['point_cloud'][-1,0] = -1
		self.data['last_transform'] = np.eye(4)
		self.data['raycast_src'] = None
		self.data['curr_datetime'] = None
		self.data['vert_pixel_scale'] = None
		self.data['horiz_pixel_scale'] = None
		self.opts['sensor_colour']['value'] = colour

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		self.data['raycast_src'] = args[0]

	def setScale(self, horizontal_size, vertical_size):
		self.data['horiz_pixel_scale'] = horizontal_size/360
		self.data['vert_pixel_scale'] = vertical_size/180

	def setCurrentDatetime(self, dt:dt.datetime) -> None:
		self.data['curr_datetime'] = dt

	def _calcLowRes(self, true_resolution:tuple[int,int]) -> tuple[int,int]:
		lowres = [0,0]
		max_1D_resolution = 240
		aspect_ratio = true_resolution[0]/true_resolution[1]
		if aspect_ratio > 1:
			lowres = (max_1D_resolution, int(max_1D_resolution/aspect_ratio))
		elif aspect_ratio < 1:
			lowres = (int(max_1D_resolution/aspect_ratio), max_1D_resolution)
		else:
			lowres = (max_1D_resolution, max_1D_resolution)
		return lowres

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['pixel_projection'] = vVisuals.Markers(parent=None,
															scaling=False,
															antialias=False)
		self.visuals['pixel_projection'].set_data(pos=self.data['point_cloud'],
													edge_width=1e-9,
													face_color=colours.normaliseColour(self.opts['sensor_colour']['value']),
													edge_color=colours.normaliseColour(self.opts['sensor_colour']['value']),
													size=self.opts['sensor_pixel_size']['value'],
													symbol='o')

	def getDimensions(self) -> tuple[int, int]:
		return self.data['lowres']

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale() and self.isActive():
			T = np.eye(4)
			if quat is not None:
				rotation = Rotation.from_quat(quat) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			elif rotation is not None:
				# bf_quat -> bodyframe to cam quaternion
				rotation = Rotation.from_matrix(rotation) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			else:
				rot_mat = np.eye(3)
				as_quat = (1,0,0,0)
			self.data['curr_quat'] = as_quat
			T[0:3,0:3] = rot_mat
			T[0:3,3] = np.asarray(pos).reshape(-1,3)

			self.data['last_transform'] = T
			lats,lons = self.data['raycast_src'].rayCastFromSensorFor2D(self.data['lowres'],
																		T,
																		self.data['lowres_rays_sf'],
																		self.data['curr_datetime'])
			self._generatePolyLatLons(lats, lons)
			self._updateMarkers()
			self._clearStaleFlag()

	def _generatePolyLatLons(self, lats, lons):

		surface_coords = np.hstack((lons.reshape(-1,1),lats.reshape(-1,1)))
		surface_coords[:,0] = (surface_coords[:,0]+180) * self.data['horiz_pixel_scale']
		surface_coords[:,1] = (surface_coords[:,1]+90) * self.data['vert_pixel_scale']
		self.data['point_cloud'] = surface_coords

		return

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['sensor_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSensorConeColour,
												'widget_data': None}
		self._dflt_opts['sensor_pixel_size'] = {'value': 1,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setPixelSize,
											'widget_data': None}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		self.visuals['pixel_projection'].set_data(pos=self.data['point_cloud'],
											size=self.opts['sensor_pixel_size']['value'],
											face_color=colours.normaliseColour(self.opts['sensor_colour']['value']),
											edge_color=colours.normaliseColour(self.opts['sensor_colour']['value']))

	def setSensorConeColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['sensor_colour']['value'] = new_colour
		self._updateMarkers()

	def setPixelSize(self, size):
		self.opts['sensor_pixel_size']['value'] = size
		self._updateMarkers()

	def setSensorVisibility(self, state):
		for visual_name, visual in self.visuals.items():
			visual.visible = state
		if state:
			self._setActiveFlag()
		else:
			self._clearActiveFlag()

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True

class SensorSuiteImageAsset(base_assets.AbstractCompoundAsset):
	def __init__(self, sens_suite_dict:dict[str,Any], name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData(sens_suite_dict)
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self, sens_suite_dict:dict[str,Any]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'SensorSuite'
		self.data['sens_suite_config'] = sens_suite_dict
		self.data['curr_datetime'] = None
		self.data['curr_sun_eci'] = None
		self.data['curr_moon_eci'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		for sensor_name, sensor in self.assets.items():
			sensor.setSource(args[0])

	def setCurrentDatetime(self, curr_dt:dt.datetime) -> None:
		self.data['curr_datetime'] = curr_dt
		for asset in self.assets.values():
			asset.setCurrentDatetime(curr_dt)

	def setCurrentSunECI(self, sun_eci_pos:np.ndarray) -> None:
		self.data['curr_sun_eci'] = sun_eci_pos
		for asset in self.assets.values():
			asset.setCurrentSunECI(sun_eci_pos)

	def setCurrentMoonECI(self, moon_eci_pos:np.ndarray) -> None:
		self.data['curr_sun_eci'] = moon_eci_pos
		for asset in self.assets.values():
			asset.setCurrentMoonECI(moon_eci_pos)

	def _instantiateAssets(self) -> None:
		sensor_names = self.data['sens_suite_config'].getSensorNames()
		full_sensor_names = [f"{self.data['name']}: {sens_name}" for sens_name in sensor_names]
		for ii, sensor_name in enumerate(sensor_names):
			logger.info(f"Instantiating sensor image asset {self.data['name']}:{sensor_name}")
			sens_dict = self.data['sens_suite_config'].getSensorConfig(sensor_name)
			if sens_dict['shape'] == satplot_data_types.SensorTypes.CONE:
				# TOOD: some kind of exception
				pass
			elif sens_dict['shape'] == satplot_data_types.SensorTypes.FPA:
				self.assets[sensor_name] = SensorImageAsset(full_sensor_names[ii], sens_dict, v_parent=None)

	def _createVisuals(self) -> None:
		pass

	def getSensorByKey(self, sens_key:str) -> Sensor3DAsset:
		# key = self.data['sens_suite_config'].getSensorNames()[sens_id]
		return self.assets[sens_key]

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		if self.isStale():
			if rotation is None and quat is None:
				logger.warning(f"Rotation and quaternion passed to sensor suite: {self.data['name']} cannot both be None")
				raise ValueError(f"Rotation and quaternion passed sensor suite: {self.data['name']} cannot both be None")
			if rotation is not None and quat is not None:
				logger.warning(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")
				raise ValueError(f"Both rotation and quaternion passed to sensor suite: {self.data['name']}, don't know which one to use")

			for asset in self.assets.values():
				asset.setTransform(pos=pos, rotation=rotation, quat=quat)
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True
		for asset in self.assets.values():
			asset.removePlotOptions()

class SensorImageAsset(base_assets.AbstractSimpleAsset):
	def __init__(self, name:str|None=None, config:dict={}, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self.config = config
		self._setDefaultOptions()
		self._initData(config['bf_quat'], config['resolution'], config['fov'])
		self._instantiateAssets()
		self._createVisuals()
		self.counter = 0
		self._attachToParentView()

	def _initData(self, bf_quat:tuple[float, float, float, float], resolution:tuple[int,int], fov:tuple[float,float]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'SensorImage'
		self.data['bf_quat'] = bf_quat
		self.data['res'] = resolution
		self.data['lowres'] = self._calcLowRes(self.data['res'])
		self.data['fov'] = fov
		self.data['lens_model'] = pinhole
		# rays from each pixel in sensor frame
		self.data['lowres_rays_sf'] = self.data['lens_model'].generatePixelRays(self.data['lowres'], self.data['fov'])
		self.data['lowres_pix_per_rad'] = self.data['lens_model'].calcPixelAngularSize(self.data['lowres'], self.data['fov'])
		self.data['rays_sf'] = self.data['lens_model'].generatePixelRays(self.data['res'], self.data['fov'])
		self.data['pix_per_rad'] = self.data['lens_model'].calcPixelAngularSize(self.data['res'], self.data['fov'])
		self.data['last_transform'] = np.eye(4)
		self.data['raycast_src'] = None
		self.data['curr_datetime'] = None
		self.data['curr_sun_eci'] = None
		self.data['curr_moon_eci'] = None
		self.data['curr_quat'] = None
		self.data['mo_data'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		self.data['raycast_src'] = args[0]

	def setCurrentDatetime(self, dt:dt.datetime) -> None:
		self.data['curr_datetime'] = dt

	def setCurrentSunECI(self, sun_eci_pos:np.ndarray) -> None:
		self.data['curr_sun_eci'] = sun_eci_pos

	def setCurrentMoonECI(self, moon_eci_pos:np.ndarray) -> None:
		self.data['curr_moon_eci'] = moon_eci_pos

	def _calcLowRes(self, true_resolution:tuple[int,int]) -> tuple[int,int]:
		lowres = [0,0]
		max_1D_resolution = 480
		aspect_ratio = true_resolution[0]/true_resolution[1]
		if aspect_ratio > 1:
			lowres = (max_1D_resolution, int(max_1D_resolution/aspect_ratio))
		elif aspect_ratio < 1:
			lowres = (int(max_1D_resolution/aspect_ratio), max_1D_resolution)
		else:
			lowres = (max_1D_resolution, max_1D_resolution)
		return lowres

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		# Earth Sphere
		img_data = _generateRandomSensorData((self.data['lowres'][1], self.data['lowres'][0]))
		self.data['mo_data'] = np.zeros((self.data['lowres'][1]*self.data['lowres'][0],3))
		self.data['mo_data'][:,0] = -1
		self.visuals['image'] = vVisuals.Image(
			img_data,
			# interpolation = 'nearest',
			# texture_format="auto",
			parent=None,
		)
		self.visuals['text'] = vVisuals.Text(f"Sensor: {self.data['name']}", color='red', anchor_x='left', anchor_y='bottom')
		self.visuals['text'].pos = 5,5
		self.visuals['text'].visible = self.opts['show_sensor_name']['value']

	def getDimensions(self) -> tuple[int, int]:
		return self.data['lowres']

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()

		if self.isStale() and self.isActive():
			T = np.eye(4)
			if quat is not None:
				rotation = Rotation.from_quat(quat) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			elif rotation is not None:
				# bf_quat -> bodyframe to cam quaternion
				rotation = Rotation.from_matrix(rotation) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
			else:
				rot_mat = np.eye(3)
				as_quat = (1,0,0,0)
			self.data['curr_quat'] = as_quat
			T[0:3,0:3] = rot_mat
			T[0:3,3] = np.asarray(pos).reshape(-1,3)

			self.data['last_transform'] = T
			img_data, mo_data = self.data['raycast_src'].rayCastFromSensor(self.data['lowres'],
																self.data['lowres_pix_per_rad'],
																T,
																self.data['lowres_rays_sf'],
																self.data['curr_datetime'],
																self.data['curr_sun_eci'],
																self.data['curr_moon_eci'],
																draw_eclipse=self.opts['solar_lighting']['value'],
																draw_atm=self.opts['plot_atmosphere']['value'],
																atm_height=self.opts['atmosphere_height']['value'],
																atm_lit_colour=self.opts['atmosphere_lit_colour']['value'],
																atm_eclipsed_colour=self.opts['atmosphere_eclipsed_colour']['value'],
																draw_sun=self.opts['plot_sun']['value'],
																sun_colour=self.opts['sun_colour']['value'],
																draw_moon=self.opts['plot_moon']['value'],
																moon_colour=self.opts['moon_colour']['value'],
																highlight_edge=self.opts['highlight_limb']['value'],
																highlight_height=self.opts['highlight_height']['value'],
																highlight_colour=self.opts['highlight_colour']['value'])
			self.data['mo_data'] = mo_data
			data_reshaped = img_data.reshape(self.data['lowres'][1],self.data['lowres'][0],3)/255
			self.visuals['image'].set_data(data_reshaped)
			# setting data of ImageVisual doesn't refresh canvas, use text visual to refresh instead
			self.visuals['text'].text = f"Sensor: {self.data['name']}"
			self._clearStaleFlag()

	def generateFullRes(self) -> tuple[np.ndarray, np.ndarray, object]:
		logger.debug(f"\tGenerating full resolution image for {self.data['name']}")
		img_data, mo_data = self.data['raycast_src'].rayCastFromSensor(self.data['res'],
															self.data['pix_per_rad'],
															self.data['last_transform'],
															self.data['rays_sf'],
															self.data['curr_datetime'],
															self.data['curr_sun_eci'],
															self.data['curr_moon_eci'],
															draw_eclipse=self.opts['solar_lighting']['value'],
															draw_atm=self.opts['plot_atmosphere']['value'],
															atm_height=self.opts['atmosphere_height']['value'],
															atm_lit_colour=self.opts['atmosphere_lit_colour']['value'],
															atm_eclipsed_colour=self.opts['atmosphere_eclipsed_colour']['value'],
															draw_sun=self.opts['plot_sun']['value'],
															sun_colour=self.opts['sun_colour']['value'],
															draw_moon=self.opts['plot_moon']['value'],
															moon_colour=self.opts['moon_colour']['value'],
															highlight_edge=self.opts['highlight_limb']['value'],
															highlight_height=self.opts['highlight_height']['value'],
															highlight_colour=self.opts['highlight_colour']['value'])
		data_reshaped = img_data.reshape(self.data['res'][1],self.data['res'][0],3)/255
		return data_reshaped, mo_data, self.getFullResMOString

	def getLowResMOString(self, fractional_pos:tuple[float, float]) -> str:
		pix_pos = int(round(fractional_pos[0]*self.data['lowres'][0])), int(round(fractional_pos[1]*self.data['lowres'][1]))
		pos_idx = np.ravel_multi_index((pix_pos[1],pix_pos[0]),(self.data['lowres'][1], self.data['lowres'][0]))
		return self._decodeLabelData(self.data['mo_data'][pos_idx])

	def getFullResMOString(self, mo_data, fractional_pos:tuple[float, float]) -> str:
		pix_pos = int(round(fractional_pos[0]*self.data['res'][0])), int(round(fractional_pos[1]*self.data['res'][1]))
		pos_idx = np.ravel_multi_index((pix_pos[1],pix_pos[0]),(self.data['res'][1], self.data['res'][0]))
		return self._decodeLabelData(mo_data[pos_idx])

	def _decodeLabelData(self, data:np.ndarray) -> str:
		if data[0] == 0:
			# geodetic
			if data[1] < 0:
				lat_hemisphere = 'S'
			elif data[1] > 0:
				lat_hemisphere = 'N'
			else:
				lat_hemisphere = ''
			if data[2] < 0:
				lon_hemisphere = 'W'
			elif data[2] > 0:
				lon_hemisphere = 'E'
			else:
				lon_hemisphere = ''
			out_str = f'Geodetic:\n{abs(data[1]):.1f}{lat_hemisphere}, {abs(data[2]):.1f}{lon_hemisphere}'
		elif data[0] == 1:
			# celestial
			raH,raM,raS = satplot_conversion.decimal2hhmmss(data[1])
			decD,decM,decS = satplot_conversion.decimal2degmmss(data[2])
			out_str = f'Celestial:\n{raH}h {raM}m {raS:.2f}s, {decD}° {decM}\' {decS:.2f}"'
		elif data[0] == 2:
			# direct str
			out_str = data[1]
		elif data[0] == -1:
			# dummy data
			out_str = f'Dummy Data'
		else:
			out_str = ''

		return out_str

	def _generateLatLonCoords(self, counter):
		lat_center = 0
		lat_fov = 45
		lon_fov = lat_fov*2
		lat = np.linspace(lat_center - lat_fov/2,lat_center + lat_fov/2, self.data['lowres'][1])
		start_lon = 0+5*counter
		lon = np.linspace(start_lon,start_lon+lon_fov, self.data['lowres'][0])
		lons,lats = np.meshgrid(lon,lat)
		lons = np.ravel(lons)
		lats = np.ravel(lats)
		return lons,lats

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['show_sensor_name'] = {'value': False,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.drawSensorName,
												'widget_data': None}
		self._dflt_opts['highlight_limb'] = {'value': False,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setHighlightLimb,
												'widget_data': None}
		self._dflt_opts['solar_lighting'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSolarLighting,
												'widget_data': None}
		self._dflt_opts['plot_atmosphere'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.drawAtmosphere,
												'widget_data': None}
		self._dflt_opts['atmosphere_height'] = {'value': 150,
										  		'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setAtmosphereHeight,
												'widget_data': None}
		self._dflt_opts['plot_sun'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.drawSun,
												'widget_data': None}
		self._dflt_opts['sun_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunColour,
												'widget_data': None}
		self._dflt_opts['plot_moon'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.drawMoon,
												'widget_data': None}
		self._dflt_opts['moon_colour'] = {'value': (159,159,159),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMoonColour,
												'widget_data': None}
		self._dflt_opts['highlight_height'] = {'value': 10,
										  		'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setHighlightHeight,
												'widget_data': None}
		self._dflt_opts['atmosphere_lit_colour'] = {'value': (168,231,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setAtmosphereLitColour,
												'widget_data': None}
		self._dflt_opts['atmosphere_eclipsed_colour'] = {'value': (23,32,35),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setAtmosphereEclipsedColour,
												'widget_data': None}
		self._dflt_opts['highlight_colour'] = {'value': (225,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setHighlightColour,
												'widget_data': None}

		self.opts = self._dflt_opts.copy()

	def redrawWithNewSettings(self) -> None:
		img_data, mo_data = self.data['raycast_src'].rayCastFromSensor(self.data['lowres'],
															self.data['lowres_pix_per_rad'],
															self.data['last_transform'],
															self.data['lowres_rays_sf'],
															self.data['curr_datetime'],
															self.data['curr_sun_eci'],
															self.data['curr_moon_eci'],
															draw_eclipse=self.opts['solar_lighting']['value'],
															draw_atm=self.opts['plot_atmosphere']['value'],
															atm_height=self.opts['atmosphere_height']['value'],
															atm_lit_colour=self.opts['atmosphere_lit_colour']['value'],
															atm_eclipsed_colour=self.opts['atmosphere_eclipsed_colour']['value'],
															draw_sun=self.opts['plot_sun']['value'],
															sun_colour=self.opts['sun_colour']['value'],
															draw_moon=self.opts['plot_moon']['value'],
															moon_colour=self.opts['moon_colour']['value'],
															highlight_edge=self.opts['highlight_limb']['value'],
															highlight_height=self.opts['highlight_height']['value'],
															highlight_colour=self.opts['highlight_colour']['value'])
		self.data['mo_data'] = mo_data
		data_reshaped = img_data.reshape(self.data['lowres'][1],self.data['lowres'][0],3)/255
		self.visuals['image'].set_data(data_reshaped)
		# setting data of ImageVisual doesn't refresh canvas, use text visual to refresh instead
		self.visuals['text'].text = f"Sensor: {self.data['name']}"

	#----- OPTIONS CALLBACKS -----#
	def drawSensorName(self, state:bool) -> None:
		self.opts['show_sensor_name']['value'] = state
		self.visuals['text'].visible = state

	def setHighlightLimb(self, state:bool) -> None:
		self.opts['highlight_limb']['value'] = state
		self.redrawWithNewSettings()

	def setHighlightHeight(self, height:bool) -> None:
		self.opts['highlight_height']['value'] = height
		self.redrawWithNewSettings()

	def setSolarLighting(self, state:bool) -> None:
		self.opts['solar_lighting']['value'] = state
		self.redrawWithNewSettings()

	def drawAtmosphere(self, state:bool) -> None:
		self.opts['plot_atmosphere']['value'] = state
		self.redrawWithNewSettings()

	def setAtmosphereHeight(self, height:bool) -> None:
		self.opts['atmosphere_height']['value'] = height
		self.redrawWithNewSettings()

	def drawSun(self, state:bool) -> None:
		self.opts['plot_sun']['value'] = state
		self.redrawWithNewSettings()

	def setSunColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['sun_colour']['value'] = new_colour
		self.redrawWithNewSettings()

	def drawMoon(self, state:bool) -> None:
		self.opts['plot_moon']['value'] = state
		self.redrawWithNewSettings()

	def setMoonColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['moon_colour']['value'] = new_colour
		self.redrawWithNewSettings()


	def setHighlightColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['highlight_colour']['value'] = new_colour
		self.redrawWithNewSettings()

	def setAtmosphereLitColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['atmosphere_lit_colour']['value'] = new_colour
		self.redrawWithNewSettings()

	def setAtmosphereEclipsedColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['atmosphere_eclipsed_colour']['value'] = new_colour
		self.redrawWithNewSettings()

	def removePlotOptions(self) -> None:
		for opt_key, opt in self.opts.items():
			if opt['widget_data'] is not None:
				logger.debug(f"marking {opt_key} for removal")
				opt['widget_data']['mark_for_removal'] = True

def _generateRandomSensorData(shape, dtype=np.float32):
    rng = np.random.default_rng()
    s = [val for val in shape]
    s.append(3)
    data = rng.random(s, dtype=dtype)
    return data