
import numpy as np
import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import SimpleAsset
from satplot.visualiser.controls import console

import satplot.model.geometry.polyhedra as polyhedra

from vispy.visuals import transforms as vTransforms
import vispy.scene.visuals as vVisuals
import vispy.visuals.filters as vFilters

from scipy.spatial.transform import Rotation

class SensorSuite(SimpleAsset):
	def __init__(self, sens_suite_dict, v_parent=None):
		super().__init__(v_parent)
		
		self._setDefaultOptions()
		self._initData()
		
		self.setSource(sens_suite_dict)
		self._instantiateAssets()
		self._createVisuals()	
		self.attachToParentView()
		
	def _initData(self):
		pass
		
	def setSource(self, *args, **kwargs):
		self.data['sens_suite_dict'] = args[0]

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		for ii in range(len(self.data['sens_suite_dict']['spacecraft']['sensors'].keys())):			
			sens_name = list(self.data['sens_suite_dict']['spacecraft']['sensors'].keys())[ii]
			sens_dict = list(self.data['sens_suite_dict']['spacecraft']['sensors'].values())[ii]
			if sens_dict['shape'] == 'cone':
				self.assets[sens_name] = Sensor.cone(sens_name, sens_dict, parent=self.data['v_parent'])
			elif sens_dict['shape'] == 'square_pyramid':
				self.assets[sens_name] = Sensor.squarePyramid(sens_name, sens_dict, parent=self.data['v_parent'])
			self.opts[f'plot_{sens_name}'] = {'value': True,
											'type': 'boolean',
											'help': '',
											'callback': self.assets[sens_name].setVisibility}

	def setTransform(self, pos=(0,0,0), rotation=None, quat=None):
		if rotation is None and quat is None:
			raise ValueError("Rotation and quaternion passed sensor suite cannot both be None")
		if rotation is not None and quat is not None:
			raise ValueError("Both rotation and quaternion passed to sensor suite, don't know which one to use")
		for asset in self.assets.values():
			asset.setTransform(pos=pos, rotation=rotation, quat=quat)

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()

class Sensor(SimpleAsset):
	def __init__(self, sensor_name, mesh_verts, mesh_faces,
			  			bf_quat, colour, sens_type=None, v_parent=None, *args, **kwargs):
		super().__init__(v_parent)
		self._setDefaultOptions()
		self._initData()
		
		self.data['type'] = sens_type
		if self.data['type'] is None:
			raise ValueError('Sensor() should not be called directly, use one of the constructor methods')		

		self.setSource(sensor_name, mesh_verts, mesh_faces, bf_quat, colour)

		self._instantiateAssets()
		self._createVisuals()
		self.setTransform()
		self.attachToParentView()
		
	def _initData(self):
		self.data['type'] = None
		self.data['name'] = None
		self.data['vertices'] = None
		self.data['faces'] = None
		self.data['bf_quat'] = None

	def setSource(self, *args, **kwargs):
		self.data['name'] = args[0]
		self.data['mesh_vertices'] = args[1]
		self.data['mesh_faces'] = args[2]
		self.data['bf_quat'] = args[3]
		self.opts['sensor_cone_colour']['value'] = args[4]

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		self.visuals['sensor_cone'] = vVisuals.Mesh(self.data['mesh_vertices'],
    											self.data['mesh_faces'],
    											color=colours.normaliseColour(self.opts['sensor_cone_colour']['value']),
    											parent=None)
		self.setTransform(rotation=Rotation.from_quat(self.data['bf_quat']).as_matrix().reshape(3,3))
		wireframe_filter = vFilters.WireframeFilter(width=1)
		alpha_filter = vFilters.Alpha(self.opts['sensor_cone_alpha']['value'])
		self.visuals['sensor_cone'].attach(alpha_filter)
		self.visuals['sensor_cone'].attach(wireframe_filter)

	def setTransform(self, pos=(0,0,0), rotation=None, quat=None):
		print(f"sensor:{self.data['name']} parent {self.data['v_parent']}")
		print(f"\tmesh parent: {self.visuals['sensor_cone'].parent}")
		print(f"\tmesh visible: {self.visuals['sensor_cone'].visible}")
		T = np.eye(4)
		if quat is not None:
			rotation = Rotation.from_quat(self.data['bf_quat']) * Rotation.from_quat(quat)
			rot_mat = rotation.as_matrix()
			# print(f"sensor:{self.data['name']} body frame quat {self.data['bf_quat']}")
			# print(f"sensor:{self.data['name']} sc quat {quat}")
			# print(f"sensor:{self.data['name']} net quat {rotation.as_quat}")
			# print("")
			# rotation = Rotation.from_quat(new_quat).as_matrix()[0]
		elif rotation is not None:
			rot_mat = np.eye(3)
		else:
			rotation = Rotation.from_quat(self.data['bf_quat'])
			rot_mat = rotation.as_matrix()
			# print(f"sensor:{self.data['name']} body frame quat {self.data['bf_quat']}")
		T[0:3,0:3] = rot_mat
		T[3,0:3] = np.asarray(pos).reshape(-1,3)
		self.visuals['sensor_cone'].transform = vTransforms.linear.MatrixTransform(T)

		for asset in self.assets.values():
			asset.setTransform(pos=pos, rotation=rotation, quat=quat)

	def _setDefaultOptions(self):
		self._dflt_opts = {}

		self._dflt_opts['sensor_cone_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'callback': self.setSensorConeColour}
		self._dflt_opts['sensor_cone_alpha'] = {'value': 0.5,
										  		'type': 'number',
												'help': '',
												'callback': self.setSensorConeAlpha}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setSensorConeColour(self, new_colour):		
		self.opts['sensor_cone_colour']['value'] = new_colour
		self.visuals['sensor_cone'].set_data(color=colours.normaliseColour(new_colour))

	def setSensorConeAlpha(self, alpha):
		raise NotImplementedError


	@classmethod
	def cone(cls, sensor_name, sensor_dict, parent=None):
		mesh_verts, mesh_faces  = polyhedra.calcConeMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['opening_angle'])
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='cone', v_parent=parent)

	@classmethod
	def squarePyramid(cls, sensor_name, sensor_dict, parent=None):
		mesh_verts, mesh_faces  = polyhedra.calcSquarePyramidMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['height_opening_angle'],
										sensor_dict['width_opening_angle'],
										axis_sample=2)
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='square_pyramid', v_parent=parent)

