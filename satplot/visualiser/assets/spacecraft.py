import numpy as np
from scipy.spatial.transform import Rotation
from typing import Any
from vispy import scene
from vispy.scene.widgets.viewbox import ViewBox

import satplot.visualiser.assets.sensors as sensors
import satplot.visualiser.colours as colours
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.gizmo as gizmo
import spherapy.orbit as orbit


class Spacecraft3DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None, sens_suites:dict[str,Any]|None=None):
		super().__init__(name, v_parent)		
		self._setDefaultOptions()
		self._initData()

		if sens_suites is not None and type(sens_suites) is not dict:
			raise TypeError(f"sens_suites is not a dict -> {sens_suites}")
		self.data['sens_suites'] = sens_suites
		if sens_suites is not None:
			self.data['num_sens_suites'] = len(sens_suites.keys())
		else:
			self.data['num_sens_suites'] = 0

		self.data['pointing_defined'] = False

		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Spacecraft'
		self.data['sens_suites'] = {}
		self.data['num_sens_suites'] = 0
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self.data['pointing'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] orbit
		# args[1] pointing
		# args[2] pointing frame transformation direction
			# True = ECI->BF
			# False = BF->ECI

		if len(args) > 1:
			self.data['pointing_defined'] = True
		else:
			self.data['pointing_defined'] = False

		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]

		if type(first_sat_orbit) is not orbit.Orbit:
			raise TypeError(f"setSource() of {self} requires a satellite dictionary, not: {first_sat_orbit}")
		self.data['coords'] = first_sat_orbit.pos
		print(f'Setting source:coordinates for {self}')

		if hasattr(first_sat_orbit,'name'):
			self.data['strings'] = [first_sat_orbit.name]
		else:
			self.data['strings'] = ['']

		if self.data['pointing_defined']:
			pointings_dict = args[1]
			first_sat_pointings = list(pointings_dict.values())[0]
			invert_transform = args[2]
			if type(first_sat_pointings) is not np.ndarray:
				raise TypeError(f"setSource() of {self} requires a pointings dictionary, not: {first_sat_pointings}")
			self.data['pointing'] = first_sat_pointings
			self.data['pointing_invert_transform'] = invert_transform
			print(f'Setting source:attitudes for {self}')
		else:
			self.data['pointing'] = None
			self.data['pointing_invert_transform'] = None

	def _instantiateAssets(self) -> None:
		self.assets['body_frame'] = gizmo.BodyGizmo(scale=700,
													width=3,
													v_parent=self.data['v_parent'])
		for key, value in self.data['sens_suites'].items():
			self.assets[f'sensor_suite_{key}'] = sensors.SensorSuite3DAsset(value,
																	name=key,
													 				v_parent=self.data['v_parent'])
		self._addIndividualSensorSuitePlotOptions()

	def _createVisuals(self) -> None:
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
												 		antialias=0)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['spacecraft_marker_colour']['value']),
										edge_color='white',
										size=self.opts['spacecraft_marker_size']['value'],
										symbol='o')
		# self.visuals['vector'] = scene.visuals.Line(self.data['v_coords'], color=colours.normaliseColour((255,0,255)),
		# 											parent=None)
		# self.visuals['vector_st'] = scene.visuals.Line(self.data['v_coords_st'], color=colours.normaliseColour((0,255,255)),
		# 											parent=None)
		

	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			# set marker position
			self._updateMarkers()
			
			if self.data['pointing_defined']:
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
						else:
							rotation = np.eye(3)
					if not non_nan_found:
						# look backwards
						for ii in range(self.data['curr_index'], -1, -1):
							if np.all(np.isnan(self.data['pointing'][ii,:])==False):
								quat = self.data['pointing'][ii,:].reshape(-1,4)
								rotation = Rotation.from_quat(quat).as_matrix()
								break
							else:
								rotation = np.eye(3)
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

				# recomputeRedraw child assets
				self._recomputeRedrawChildren(pos=self.data['coords'][self.data['curr_index']].reshape(1,3), rotation=rotation)
			else:
				self._recomputeRedrawChildren(pos=self.data['coords'][self.data['curr_index']].reshape(1,3))
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		curr_world_pos = (self.data['coords'][self.data['curr_index']]).reshape(1,3)
		canvas_pos = self.visuals['marker'].get_transform('visual','canvas').map(curr_world_pos)
		canvas_pos /= canvas_pos[:,3:]
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(canvas_pos[0,0], canvas_pos[0,1])]
		mo_info['world_pos'] = [curr_world_pos]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]
		return mo_info
		# return [(canvas_pos[0,0], canvas_pos[0,1])], ['SpIRIT']

	def setAttitudeAssetsVisibility(self, state):
		self.setBodyFrameVisibility(state)
		self.setAllSensorSuitesVisibility(state)

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_spacecraft'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setVisibility}		
		self._dflt_opts['spacecraft_marker_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setMarkerColour}
		self._dflt_opts['plot_spacecraft_marker'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalMarkerVisibility}
		self._dflt_opts['spacecraft_marker_size'] = {'value': 500,
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
	def setMarkerColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['spacecraft_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setAllSensorSuitesVisibility(self, state:bool) -> None:
		for key, asset in self.assets.items():
			if isinstance(asset, sensors.SensorSuite3DAsset):
				asset.setVisibilityRecursive(state)

	def setOrbitalMarkerVisibility(self, state:bool) -> None:
		self.visuals['marker'].visible = state

	def setBodyFrameVisibility(self, state:bool) -> None:
		self.assets['body_frame'].setVisibility(state)

	def setOrbitalMarkerSize(self, value:int) -> None:
		self.opts['spacecraft_marker_size']['value'] = value
		self._updateMarkers()

	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['spacecraft_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_marker_colour']['value']))

	#----- HELPER FUNCTIONS -----#
	def _addIndividualSensorSuitePlotOptions(self) -> None:
		for key, value in self.data['sens_suites'].items():
			self.opts[f'plot_sensor_suite_{key}'] = {'value': True,
													'type': 'boolean',
													'help': '',
													'callback': self.assets[f'sensor_suite_{key}'].setVisibility}
			