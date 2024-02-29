
import numpy as np
import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.controls import console

import satplot.model.geometry.polyhedra as polyhedra

from vispy.visuals import transforms as vTransforms
import vispy.scene.visuals as vVisuals
import vispy.visuals.filters as vFilters

from scipy.spatial.transform import Rotation

class SensorSuite(BaseAsset):
	def __init__(self, sens_suite_dict, canvas=None, parent=None):

		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False

		self.parent = parent
		self.data['sens_suite_dict'] = sens_suite_dict
		self._setDefaultOptions()
		self.draw()

		
	def compute(self):
		pass

	def draw(self):
		for ii in range(len(self.data['sens_suite_dict']['spacecraft']['sensors'].keys())):
			
			sens_name = list(self.data['sens_suite_dict']['spacecraft']['sensors'].keys())[ii]
			sens_dict = list(self.data['sens_suite_dict']['spacecraft']['sensors'].values())[ii]
			print(f"Creating sensor {sens_name}")
			if sens_dict['shape'] == 'cone':
				self.visuals[sens_name] = Sensor.cone(sens_name, sens_dict, parent=self.parent)
			elif sens_dict['shape'] == 'square_pyramid':
				self.visuals[sens_name] = Sensor.squarePyramid(sens_name, sens_dict, parent=self.parent)
			self.opts[f'plot_{sens_name}'] = {'value': True,
											'type': 'boolean',
											'help': '',
											'callback': self.visuals[sens_name].setSensorAssetVisibility}

	def recompute(self):
		pass

	def setTransform(self, pos=(0,0,0), rotation=None, quat=None):
		if rotation is None and quat is None:
			raise ValueError("Rotation and quaternion passed sensor suite cannot both be None")
		if rotation is not None and quat is not None:
			raise ValueError("Both rotation and quaternion passed to sensor suite, don't know which one to use")
		for sens_name, sensor in self.visuals.items():
			sensor.setTransform(pos=pos, rotation=rotation, quat=quat)

	def setVisibility(self, state):
		for sens_name, sensor in self.visuals.items():
			sensor.setSensorAssetVisibility(state)
		# self.visuals['gizmo'].visible = state

	def _setDefaultOptions(self):
		self._dflt_opts = {}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass

	def setSensorSuiteAssetVisibility(self, state):
		raise NotImplementedError

class Sensor(BaseAsset):
	def __init__(self, sensor_name, mesh_verts, mesh_faces,
			  			bf_quat, colour, sens_type=None, parent=None, *args, **kwargs):

		self.type = sens_type
		print(self.type)
		if self.type is None:
			raise ValueError('Sensor() should not be called directly, use one of the constructor methods')
		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False
		self._setDefaultOptions()

		print(f"sensor parent passed to init:{parent}")
		self.parent = parent
		print(f"sensor parent set in init:{self.parent}")
		self.name = sensor_name
		self.type = type
		self.data['sensor_cone_vertices'] = mesh_verts
		self.data['sensor_cone_faces'] = mesh_faces
		self.data['bf_quat'] = bf_quat
		print(f"sensor:{self.name} body frame quat {self.data['bf_quat']}")
		self.opts['sensor_cone_colour']['value'] = colour

		self.draw()
		
	def compute(self):
		pass

	def draw(self):
		self.addSensorCone()
		self.setTransform()

	def recompute(self):
		pass

	def addSensorCone(self):
		self.visuals['sensor_cone'] = vVisuals.Mesh(self.data['sensor_cone_vertices'],
    											self.data['sensor_cone_faces'],
    											color=colours.normaliseColour(self.opts['sensor_cone_colour']['value']),
    											parent=self.parent)
		self.setTransform(rotation=Rotation.from_quat(self.data['bf_quat']).as_matrix().reshape(3,3))
		print(f"sensor parent:{self.parent}")
		wireframe_filter = vFilters.WireframeFilter(width=1)
		alpha_filter = vFilters.Alpha(self.opts['sensor_cone_alpha']['value'])
		self.visuals['sensor_cone'].attach(alpha_filter)
		self.visuals['sensor_cone'].attach(wireframe_filter)

	def setTransform(self, pos=(0,0,0), rotation=None, quat=None):
		T = np.eye(4)
		if quat is not None:
			rotation = Rotation.from_quat(self.data['bf_quat']) * Rotation.from_quat(quat)
			rot_mat = rotation.as_matrix()
			print(f"sensor:{self.name} body frame quat {self.data['bf_quat']}")
			print(f"sensor:{self.name} sc quat {quat}")
			print(f"sensor:{self.name} net quat {rotation.as_quat}")
			print("")
			# rotation = Rotation.from_quat(new_quat).as_matrix()[0]
		elif rotation is not None:
			rot_mat = np.eye(3)
		else:
			rotation = Rotation.from_quat(self.data['bf_quat'])
			rot_mat = rotation.as_matrix()
			print(f"sensor:{self.name} body frame quat {self.data['bf_quat']}")
		T[0:3,0:3] = rot_mat
		T[3,0:3] = np.asarray(pos).reshape(-1,3)
		self.visuals['sensor_cone'].transform = vTransforms.linear.MatrixTransform(T)

	def setVisibility(self, state):
		pass
		# self.visuals['gizmo'].visible = state

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
		self._createOptHelp()

	def setSensorConeColour(self, new_colour):		
		self.opts['sensor_cone_colour']['value'] = new_colour
		self.visuals['sensor_cone'].set_data(color=colours.normaliseColour(new_colour))

	def setSensorConeAlpha(self, alpha):
		raise NotImplementedError

	def _createOptHelp(self):
		pass

	def setSensorAssetVisibility(self, state):
		self.visuals['sensor_cone'].visible = state
	
	@classmethod
	def cone(cls, sensor_name, sensor_dict, parent=None):
		print(f"sensor parent passed to constructor:{parent}")
		mesh_verts, mesh_faces  = polyhedra.calcConeMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['opening_angle'])
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='cone', parent=parent)

	@classmethod
	def squarePyramid(cls, sensor_name, sensor_dict, parent=None):
		print(f"sensor parent passed to constructor:{parent}")
		mesh_verts, mesh_faces  = polyhedra.calcSquarePyramidMesh((0,0,0),
								  		sensor_dict['range'],
										(1,0,0),
										sensor_dict['height_opening_angle'],
										sensor_dict['width_opening_angle'],
										axis_sample=2)
		
		bf_quat = np.asarray([float(x) for x in sensor_dict['bf_quat'].replace('(','').replace(')','').split(',')]).reshape(1,4)
		colour = [int(x) for x in sensor_dict['colour'].replace('(','').replace(')','').split(',')]
		return cls(sensor_name, mesh_verts, mesh_faces, bf_quat, colour, sens_type='square_pyramid', parent=parent)
