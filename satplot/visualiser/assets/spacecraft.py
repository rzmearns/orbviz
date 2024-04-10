import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import gizmo

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons
import satplot.model.orbit as orbit

import satplot.visualiser.controls.console as console
import satplot.visualiser.assets.sensors as sensors
from scipy.spatial.transform import Rotation

import geopandas as gpd

from vispy import scene, color
from vispy.visuals import transforms as vTransforms

import numpy as np

class SpacecraftVisualiser(BaseAsset):
	def __init__(self, name=None, v_parent=None, sens_suites=None):
		super().__init__(name, v_parent)		
		self._setDefaultOptions()
		self._initData()

		if sens_suites is not None and type(sens_suites) is not dict:
			raise TypeError(f"sens_suites is not a dict -> {sens_suites}")
		self.data['sens_suites'] = sens_suites
		self.data['num_sens_suites'] = len(sens_suites.keys())

		self._instantiateAssets()
		self._createVisuals()

		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Spacecraft'
		self.data['sens_suites'] = []
		self.data['num_sens_suites'] = 0
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self.data['pointing'] = None
		# self.data['v_coords'] = 10000*np.array([[0, 0, 0],[-.01736, 0, 0.9848]]) # -Sun
		# self.data['v_coords_st'] = 10000*np.array([[0, 0, 0],[-.01736, 0, 0.9848]]) # -Sun
		self.data['v_coords'] = 10000*np.array([[0, 0, 0],[0.433, 0.75, -0.5]]) #-Cam4
		self.data['v_coords_st'] =  20000*np.array([[0, 0, 0],[0.433, 0.75, -0.5]]) 

	def setSource(self, *args, **kwargs):
		# args[0] orbit
		# args[1] pointing
		# args[2] pointing frame transformation direction
			# True = ECI->BF
			# False = BF->ECI
		if type(args[0]) is not orbit.Orbit:
			raise TypeError(f"args[0]:orbit is not a satplot Orbit -> {args[0]}")
		self.data['coords'] = args[0].pos

		if type(args[1]) is not np.ndarray:
			raise TypeError(f"args[1]:pointing is not an ndarray -> {args[1]}")
		self.data['pointing'] = args[1]
		self.data['pointing_invert_transform'] = args[2]


	def _instantiateAssets(self):
		self.assets['body_frame'] = gizmo.BodyGizmo(scale=700,
													width=3,
													v_parent=self.data['v_parent'])
		for key, value in self.data['sens_suites'].items():
			self.assets[f'sensor_suite_{key}'] = sensors.SensorSuite(value,
																	name=key,
													 				v_parent=self.data['v_parent'])
		self._addIndividualSensorSuitePlotOptions()

	def _createVisuals(self):
		self.visuals['marker'] = scene.visuals.Markers(scaling=True,
												 		antialias=0,
														parent=None)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['spacecraft_point_colour']['value']),
										edge_color='white',
										size=self.opts['spacecraft_point_size']['value'],
										symbol='o')
		# self.visuals['vector'] = scene.visuals.Line(self.data['v_coords'], color=colours.normaliseColour((255,0,255)),
		# 											parent=None)
		# self.visuals['vector_st'] = scene.visuals.Line(self.data['v_coords_st'], color=colours.normaliseColour((0,255,255)),
		# 											parent=None)
		

	# Use BaseAsset.updateIndex()

	def recompute(self):
		if self.first_draw:
			self.first_draw = False
		if self.requires_recompute:
			# set marker position
			self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['spacecraft_point_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_point_colour']['value']))
			
			# set gizmo and sensor orientations
			#TODO: This check for last/next good pointing could be done better
			if np.any(np.isnan(self.data['pointing'][self.data['curr_index'],:])):
				non_nan_found = False
				# look forwards
				for ii in range(self.data['curr_index'], len(self.data['pointing'])):
					if np.all(np.isnan(self.data['pointing'][ii,:])==False):
						non_nan_found = True
						quat = self.data['pointing'][ii,:].reshape(-1,4)
						rotation = Rotation.from_quat(quat).as_matrix()
						break			
				if not non_nan_found:
					# look backwards
					for ii in range(self.data['curr_index'], -1, -1):
						if np.all(np.isnan(self.data['pointing'][ii,:])==False):
							quat = self.data['pointing'][ii,:].reshape(-1,4)
							rotation = Rotation.from_quat(quat).as_matrix()
							break
				self.assets['body_frame'].setTemporaryGizmoXColour((255,0,255))
				self.assets['body_frame'].setTemporaryGizmoYColour((255,0,255))
				self.assets['body_frame'].setTemporaryGizmoZColour((255,0,255))
			else:
				quat = self.data['pointing'][self.data['curr_index']].reshape(-1,4)
				if self.data['pointing_invert_transform']:
					# Quat = ECI->BF
					rotation = Rotation.from_quat(quat).as_matrix()
				else:
					# Quat = BF->ECI
					rotation = Rotation.from_quat(quat).inv().as_matrix()
				self.assets['body_frame'].restoreGizmoColours()

			self.assets['body_frame'].setTransform(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
										   			rotation=rotation)
			vp = rotation.reshape(3,3).dot(self.data['v_coords'].T).T
			print(f"{vp=}")
			svp = vp
			print(f"{svp=}")
			v = svp+self.data['coords'][self.data['curr_index']].reshape(1,3)
			print(f"{v=}")
			# using set transform
			T = T = np.eye(4)
			T[0:3,0:3] = rotation
			T[3,0:3] = np.asarray(self.data['coords'][self.data['curr_index']].reshape(1,3))
			# self.visuals['vector_st'].transform = vTransforms.linear.MatrixTransform(T.T)
			
			print(f"Rotation {rotation}, reshape {rotation.reshape(3,3)}")
			# pos = rotation.reshape(3,3).dot(self.data['v_coords'].T).T + self.data['coords'][self.data['curr_index']].reshape(1,3)
			# print(f"Rotated vector: {pos[1,:]-self.data['coords'][self.data['curr_index']].reshape(1,3)}")
			# print(pos)
			print(f"Spacecraft position: {self.data['coords'][self.data['curr_index']].reshape(1,3)}")
			# self.visuals['vector'].set_data(v)
			for key, value in self.data['sens_suites'].items():			
				self.assets[f'sensor_suite_{key}'].setTransform(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
										   						rotation=rotation)
			
			self.childAssetsRecompute()
			self.requires_recompute = False

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_spacecraft'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setVisibility}		
		self._dflt_opts['spacecraft_point_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'callback': self.setMarkerColour}
		self._dflt_opts['plot_spacecraft_point'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalMarkerVisibility}
		self._dflt_opts['spacecraft_point_size'] = {'value': 250,
										  		'type': 'number',
												'help': '',
												'callback': self.setOrbitalMarkerSize}
		self._dflt_opts['plot_body_frame'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'callback': self.setBodyFrameVisibility}
		self._dflt_opts['plot_all_sensor_suites'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'callback': self.setAllSensorSuitesVisibility}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setMarkerColour(self, new_colour):
		self.opts['spacecraft_point_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['marker'].set_data(face_color=colours.normaliseColour(new_colour))

	def setAllSensorSuitesVisibility(self, state):
		for key, asset in self.assets.items():
			key_split = key.split('_')
			if key_split[0] == 'sensor' and key_split[1] == 'suite':
				asset.setVisibility(state)

	def setOrbitalMarkerVisibility(self, state):
		self.visuals['marker'].visible = state

	def setBodyFrameVisibility(self, state):
		self.assets['body_frame'].setVisibility(state)

	def setOrbitalMarkerSize(self, value):
		self.opts['spacecraft_point_size']['value'] = value
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['spacecraft_point_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_point_colour']['value']))
		self.visuals['marker'].update()

	#----- HELPER FUNCTIONS -----#
	def _addIndividualSensorSuitePlotOptions(self):
		for key, value in self.data['sens_suites'].items():
			self.opts[f'plot_sensor_suite_{key}'] = {'value': True,
													'type': 'boolean',
													'help': '',
													'callback': self.assets[f'sensor_suite_{key}'].setVisibility}
			