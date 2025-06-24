import datetime as dt
import logging
import numpy as np
import numpy.typing as nptyping
from scipy.spatial.transform import Rotation
from typing import Any

import vispy.scene.visuals as vVisuals
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.filters as vFilters
import vispy.visuals.transforms as vTransforms
from vispy.util.quaternion import Quaternion

import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.data_models.data_types as satplot_data_types
import satplot.model.lens_models.pinhole as pinhole
import satplot.util.constants as c
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
			print(f'{sensor=}')
			sens_dict = self.data['sens_suite_config'].getSensorConfig(sensor)
			if sens_dict['shape'] == satplot_data_types.SensorTypes.CONE:
				self.assets[sensor] = Sensor3DAsset.cone(sensor, sens_dict, parent=self.data['v_parent'])
			elif sens_dict['shape'] == satplot_data_types.SensorTypes.FPA:
				self.assets[sensor] = Sensor3DAsset.squarePyramid(sensor, sens_dict, parent=self.data['v_parent'])

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

	def setSuiteVisibility(self, state:bool) -> None:
		self.setVisibilityRecursive(state)

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
		
	def _initData(self, sens_type:str, sensor_name:str, mesh_verts:nptyping.NDArray, mesh_faces:nptyping.NDArray, bf_quat:nptyping.NDArray, colour:tuple[float,float,float]):
		self.data['type'] = sens_type
		self.data['name'] = sensor_name
		self.data['mesh_vertices'] = mesh_verts
		self.data['mesh_faces'] = mesh_faces
		self.data['bf_quat'] = bf_quat
		self.data['vispy_quat'] = self.data['bf_quat']
		print(f"{self.data['vispy_quat']=}")
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
											'widget': None}
		self._dflt_opts['sensor_cone_alpha'] = {'value': 0.5,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSensorConeAlpha,
											'widget': None}

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

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		for sensor_name, sensor in self.assets.items():
			sensor.setSource(args[0])

	def setCurrentDatetime(self, dt:dt.datetime) -> None:
		self.data['curr_datetime'] = dt
		for asset in self.assets.values():
			asset.setCurrentDatetime(dt)

	def _instantiateAssets(self) -> None:
		sensor_names = self.data['sens_suite_config'].getSensorNames()
		for sensor_name in sensor_names:
			print(f'{sensor_name=}')
			sens_dict = self.data['sens_suite_config'].getSensorConfig(sensor_name)
			if sens_dict['shape'] == satplot_data_types.SensorTypes.CONE:
				# TOOD: some kind of exception
				pass
			elif sens_dict['shape'] == satplot_data_types.SensorTypes.FPA:
				self.assets[sensor_name] = SensorImageAsset(sensor_name, sens_dict, v_parent=None)

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

	def setSuiteVisibility(self, state:bool) -> None:
		self.setVisibilityRecursive(state)

class SensorImageAsset(base_assets.AbstractSimpleAsset):
	def __init__(self, name:str|None=None, config:dict={}, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self.config = config
		self._setDefaultOptions()
		self._initData(config['bf_quat'], config['resolution'], config['fov'])
		self._instantiateAssets()
		self._createVisuals()
		self.counter = 0
		# These callbacks need to be set after asset creation as the option dict is populated during draw()
		print(f'Created SensorImage asset')
		self._attachToParentView()

	def _initData(self, bf_quat:tuple[float, float, float, float], resolution:tuple[int,int], fov:tuple[float,float]) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'SensorImage'
		self.data['bf_quat'] = bf_quat
		self.data['res'] = resolution
		self.data['lowres'] = self._calcLowRes(self.data['res'])
		self.data['fov'] = (62.2, 48.8)
		self.data['lens_model'] = pinhole
		# rays from each pixel in sensor frame
		self.data['rays_sf'] = self.data['lens_model'].generatePixelRays(self.data['lowres'], self.data['fov'])

	def setSource(self, *args, **kwargs) -> None:
		# args[0] = raycast_src
		self.data['raycast_src'] = args[0]

	def setCurrentDatetime(self, dt:dt.datetime) -> None:
		self.data['curr_datetime'] = dt

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
		self.visuals['image'] = vVisuals.Image(
			img_data,
			# interpolation = 'nearest',
			# texture_format="auto",
			parent=None,
		)
		self.visuals['text'] = vVisuals.Text(f"Sensor: {self.data['name']}", color='red')
		self.visuals['text'].pos = self.data['lowres'][0]/2, self.data['lowres'][1]/2

	def getDimensions(self) -> tuple[int, int]:
		return self.data['lowres']

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray|None=None, quat:nptyping.NDArray|None=None) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()

		if self.isActive():
			if self.isStale():
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
				T[0:3,0:3] = rot_mat
				T[0:3,3] = np.asarray(pos).reshape(-1,3)

				data = self.data['raycast_src'].rayCastFromSensor(T,self.data['rays_sf'],self.data['curr_datetime'], atmosphere=True, highlight_edge=True)
				data_reshaped = data.reshape(self.data['lowres'][1],self.data['lowres'][0],3)/255
				self.visuals['image'].set_data(data_reshaped)
				self.visuals['text'].text = f"Sensor: {self.data['name']}: {self.counter}"
				self.counter += 1
				self._clearStaleFlag()

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
		self._dflt_opts['plot_earth'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibilityRecursive,
											'widget': None}
		self._dflt_opts['plot_earth_sphere'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setEarthSphereVisibility,
											'widget': None}
		self._dflt_opts['earth_sphere_colour'] = {'value': (220,220,220),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setEarthSphereColour,
											'widget': None}
		self._dflt_opts['plot_earth_axis'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setEarthAxisVisibility,
											'widget': None}
		self._dflt_opts['earth_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setEarthAxisColour,
											'widget': None}
		self._dflt_opts['plot_parallels'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': None,
											'widget': None}
		self._dflt_opts['plot_equator'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': None,
											'widget': None}
		self._dflt_opts['plot_meridians'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': None,
											'widget': None}
		self._dflt_opts['plot_landmass'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setLandmassVisibility,
											'widget': None}
		self._dflt_opts['landmass_colour'] = {'value': (0,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setLandMassColour,
											'widget': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setEarthSphereColour(self, new_colour:tuple[float,float,float]) -> None:
		logger.debug(f"Changing earth sphere colour {self.opts['earth_sphere_colour']['value']} -> {new_colour}")
		self.opts['earth_sphere_colour']['value'] = new_colour
		n_faces = self.visuals['earth_sphere'].mesh._meshdata.n_faces
		n_verts = self.visuals['earth_sphere'].mesh._meshdata.n_vertices
		self.visuals['earth_sphere'].mesh._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['earth_sphere'].mesh._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['earth_sphere'].mesh.mesh_data_changed()

	def setEarthAxisColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['earth_axis_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['earth_axis'].set_data(color=colours.normaliseColour(new_colour))

	def setLandMassColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['landmass_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['landmass'].set_data(color=colours.normaliseColour(new_colour))

	def setEarthAxisVisibility(self, state:bool) -> None:
		self.opts['plot_earth_axis']['value'] = state
		self.visuals['earth_axis'].visible = self.opts['plot_earth_axis']['value']

	def setLandmassVisibility(self, state:bool) -> None:
		self.opts['plot_landmass']['value'] = state
		self.visuals['landmass'].visible = self.opts['plot_landmass']['value']

	def setEarthSphereVisibility(self, state:bool) -> None:
		self.opts['plot_earth_sphere']['value'] = state
		self.visuals['earth_sphere'].visible = self.opts['plot_earth_sphere']['value']

def _generateRandomSensorData(shape, dtype=np.float32):
    rng = np.random.default_rng()
    s = [val for val in shape]
    s.append(3)
    data = rng.random(s, dtype=dtype)
    return data