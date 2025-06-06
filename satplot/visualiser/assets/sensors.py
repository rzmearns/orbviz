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
			if sens_dict['shape'] == 'cone':
				self.assets[sensor] = Sensor3DAsset.cone(sensor, sens_dict, parent=self.data['v_parent'])
			elif sens_dict['shape'] == 'square_pyramid':
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
		if sens_type is None or sens_type not in self.getValidTypes():
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
			print(f'{rotation=}')
			print(f'{quat=}')
			sc_rotation = rotation
			if quat is not None:
				rotation = Rotation.from_quat(quat) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				as_quat = rotation.as_quat()
				# as_quat = (Rotation.from_quat(self.data['bf_quat']) * Rotation.from_quat(quat)).as_quat()
			elif rotation is not None:
				# bf_quat -> bodyframe to cam quaternion
				rotation = Rotation.from_matrix(rotation) * Rotation.from_quat(self.data['bf_quat'])
				rot_mat = rotation.as_matrix()
				# as_quat = (Rotation.from_matrix(rotation) * Rotation.from_quat(self.data['bf_quat'])).as_quat()
				as_quat = rotation.as_quat()
			else:
				rot_mat = np.eye(3)
				as_quat = (1,0,0,0)
			print(f"{as_quat=}")
			self.data['vispy_quat'] = as_quat
			# if rotation is not None:
			# 	self.data['vispy_quat'] = Rotation.from_matrix(sc_rotation).inv().as_quat()
			# else:
			# 	self.data['vispy_quat'] = quat
			# self.data['vispy_quat'] = np.array((1,0,0,0))
			# self.data['vispy_quat'] = np.array((0.707,0,0,0.707))
			# self.data['vispy_quat'] = np.array((0.707,0,-0.707,0))
			print(f"{self.data['vispy_quat']=}")
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
	def getValidTypes(cls) -> list[str]:
		return ['cone','square_pyramid']

	@classmethod
	def getTypeConfigFields(cls, type:str) -> list[str]:
		if type == 'cone':
			return ['opening_angle','range','colour','bf_quat']
		elif type == 'square_pyramid':
			return ['width_opening_angle', 'height_opening_angle','range','colour','bf_quat']
		else:
			return []

	@classmethod
	def cone(cls, sensor_name:str, sensor_dict:dict[str,Any], parent:ViewBox|None=None):
		mesh_verts, mesh_faces  = polyhedra.calcConeMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['opening_angle'])
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='cone', v_parent=parent)

	@classmethod
	def squarePyramid(cls, sensor_name:str, sensor_dict:dict[str,Any], parent:ViewBox|None=None):
		mesh_verts, mesh_faces  = polyhedra.calcSquarePyramidMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['height_opening_angle'],
										sensor_dict['width_opening_angle'],
										axis_sample=2)
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='square_pyramid', v_parent=parent)

