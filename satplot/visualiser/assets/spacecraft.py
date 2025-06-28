import logging
import numpy as np
from scipy.spatial.transform import Rotation
from typing import Any
from vispy import scene
from vispy.scene.widgets.viewbox import ViewBox

import satplot.model.data_models.data_types as data_types
import satplot.model.data_models.history_data as history_data
import satplot.model.data_models.earth_raycast_data as earth_raycast_data
import satplot.visualiser.assets.sensors as sensors
import satplot.visualiser.colours as colours
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.gizmo as gizmo
import satplot.visualiser.interface.console as console
import spherapy.orbit as orbit

logger = logging.getLogger(__name__)

class Spacecraft3DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)		
		self._setDefaultOptions()
		self._initData()

		self.data['pointing_defined'] = False

		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Spacecraft'
		self.data['sens_suites'] = {}
		self.data['coords'] = np.zeros((4,3))
		self.data['strings'] = ['']
		self.data['curr_index'] = 2
		self.data['pointing'] = None
		self.data['pointing_defined'] = False
		self.data['old_pointing_defined'] = False
		self.data['pointing_invert_transform'] = False
		self.data['sc_config'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] orbit
		# args[1] pointing
		# args[2] pointing frame transformation direction
			# True = ECI->BF
			# False = BF->ECI
		# args[3] spacecraft configuration

		self.data['old_pointing_defined'] = self.data['pointing_defined']
		if args[1] is not None:

			self.data['pointing_defined'] = True
			logger.debug(f'spacecraft has pointing')
		else:
			self.data['pointing_defined'] = False
			logger.debug(f'spacecraft has NO pointing')

		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]

		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error(f"setSource() of {self} requires an {orbit.Orbit} as value of dict from args[0], not: {type(first_sat_orbit)}")
			raise TypeError(f"setSource() of {self} requires an {orbit.Orbit} as value of dict from args[0], not: {type(first_sat_orbit)}")
		self.data['coords'] = first_sat_orbit.pos
		logger.debug(f'Setting source:coordinates for {self}')

		if hasattr(first_sat_orbit,'name'):
			self.data['strings'] = [first_sat_orbit.name]
		else:
			self.data['strings'] = ['']

		if self.data['pointing_defined']:
			pointings_dict = args[1]
			first_sat_pointings = list(pointings_dict.values())[0]
			invert_transform = args[2]
			if type(first_sat_pointings) is not np.ndarray:
				logger.error(f"setSource() of {self} requires an {np.ndarray} as value of dict from args[1], not: {type(first_sat_pointings)}")
				raise TypeError(f"setSource() of {self} requires an {np.ndarray} as value of dict from args[1], not: {type(first_sat_pointings)}")
			self.data['pointing'] = first_sat_pointings
			self.data['pointing_invert_transform'] = invert_transform
			logger.debug(f'Setting source:attitudes for {self}')
		else:
			self.data['pointing'] = None
			self.data['pointing_invert_transform'] = None

		if self.data['sc_config'] is not None:
			old_suite_names = list(self.data['sc_config'].getSensorSuites().keys())
		else:
			old_suite_names = []

		if self.data['old_pointing_defined'] == self.data['pointing_defined'] and \
			self.data['sc_config'] == args[3]:
			# config has not changed -> don't need to re-instantiate sensors
			logger.debug('Spacecraft pointing related config has not changed')
			config_changed = False
			return

		if self.data['sc_config'] is not None:
			old_config_filestem = self.data['sc_config'].filestem
		else:
			old_config_filestem = None
		self.data['sc_config'] = args[3]

		if self.data['old_pointing_defined'] or \
			(self.data['sc_config'].filestem != old_config_filestem):
			# If pointing had previously been defined -> old sensors, options need to be removed
			# if no pointing, no point having sensors
			self._removeSensorAssets(old_suite_names)

		if self.data['pointing_defined']:
			self._instantiateSensorAssets()

	def _instantiateAssets(self) -> None:
		self.assets['body_frame'] = gizmo.BodyGizmo(scale=700,
													width=3,
													v_parent=self.data['v_parent'])
		if self.data['sc_config'] is not None:
			self._instantiateSensorAssets()

	def _removeSensorAssets(self, old_suite_names:list[str]) -> None:
		self._removeOldSensorSuitePlotOptions(old_suite_names)
		for suite_name in old_suite_names:
				self.assets[f'sensor_suite_{suite_name}'].removePlotOptions()
				self.assets[f'sensor_suite_{suite_name}'].detachFromParentViewRecursive()
				del(self.assets[f'sensor_suite_{suite_name}'])

	def _instantiateSensorAssets(self) -> None:
		for key, value in self.data['sc_config'].getSensorSuites().items():
			logger.debug(f'Creating sensor suite sensor_suite_{key}')
			self.assets[f'sensor_suite_{key}'] = sensors.SensorSuite3DAsset(value,
																	name=key,
													 				v_parent=self.data['v_parent'])
			self.assets[f'sensor_suite_{key}'].setVisibility(False)
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
		logger.debug(f'Setting attitude visibility')
		self.setBodyFrameVisibility(state)
		self.setAllSensorSuitesStatefulVisibility(state)

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['spacecraft_marker_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMarkerColour,
											'widget_data': None}
		self._dflt_opts['plot_spacecraft_marker'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalMarkerVisibility,
											'widget_data': None}
		self._dflt_opts['spacecraft_marker_size'] = {'value': 500,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setOrbitalMarkerSize,
											'widget_data': None}
		self._dflt_opts['plot_body_frame'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setBodyFrameVisibility,
											'widget_data': None}
		self._dflt_opts['plot_all_sensor_suites'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setAllSensorSuitesVisibility,
											'widget_data': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setMarkerColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['spacecraft_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setAllSensorSuitesVisibility(self, state:bool) -> None:
		for key, asset in self.assets.items():
			if isinstance(asset, sensors.SensorSuite3DAsset):
				asset.setVisibilityRecursive(state)

	def setAllSensorSuitesStatefulVisibility(self, state:bool) -> None:
		for key, asset in self.assets.items():
			if isinstance(asset, sensors.SensorSuite3DAsset):
				if state and self.opts[f'plot_{key}']['value']:
					# turning on, only if option state has it previously on
					asset.setVisibilityRecursive(state)
				elif not state:
					# turning off
					asset.setVisibilityRecursive(state)

	def setOrbitalMarkerVisibility(self, state:bool) -> None:
		self.opts['plot_spacecraft_marker']['value'] = state
		self.visuals['marker'].visible = self.opts['plot_spacecraft_marker']['value']

	def setBodyFrameVisibility(self, state:bool) -> None:
		self.opts['plot_body_frame']['value'] = state
		self.assets['body_frame'].setVisibility(self.opts['plot_body_frame']['value'])

	def setOrbitalMarkerSize(self, value:int) -> None:
		self.opts['spacecraft_marker_size']['value'] = value
		self._updateMarkers()

	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['spacecraft_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_marker_colour']['value']))

	#----- HELPER FUNCTIONS -----#
	def _addIndividualSensorSuitePlotOptions(self) -> None:
		logger.debug(f'Adding sensor suite options dictionary entries for:')
		for key, value in self.data['sc_config'].getSensorSuites().items():
			visibilityCallback = self._makeVisibilityCallback(key)
			self.opts[f'plot_sensor_suite_{key}'] = {'value': True,
													'type': 'boolean',
													'help': '',
													'static': False,
													'callback': visibilityCallback,
													'widget_data': None}

	def _makeVisibilityCallback(self, suite_key:str):
		def _visibilityCallback(state):
			self.opts[f'plot_sensor_suite_{suite_key}']['value'] = state
			self.assets[f'sensor_suite_{suite_key}'].setSuiteVisibility(state)
		return _visibilityCallback

	def _removeOldSensorSuitePlotOptions(self, old_suite_names:list[str]) -> None:
		for suite_name in old_suite_names:
			if self.opts[f'plot_sensor_suite_{suite_name}']['widget_data'] is not None:
				self.opts[f'plot_sensor_suite_{suite_name}']['widget_data']['mark_for_removal'] = True
			self.assets[f'sensor_suite_{suite_name}'].removePlotOptions()
			del(self.opts[f'plot_sensor_suite_{suite_name}'])

class Spacecraft2DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()

		self.data['pointing_defined'] = False

		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Spacecraft'
		self.data['strings'] = ['']
		self.data['sens_suites'] = {}
		self.data['coords'] = np.zeros((4,2))
		self.data['scaled_coords'] = np.zeros((4,2))
		self.data['curr_index'] = 2
		self.data['sc_config'] = None
		self.data['history_src'] = None
		self.data['raycast_src'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] spacecraft configuration
		# args[1] history data
		# args[2] ray cast src data

		if type(args[0]) is not data_types.SpacecraftConfig:
			logger.error(f"setSource() of {self} requires a {data_types.SpacecraftConfig} as args[0], not: {type(args[0])}")
			raise TypeError(f"setSource() of {self} requires a {data_types.SpacecraftConfig} as args[0], not: {type(args[0])}")
			return

		if type(args[1]) is not history_data.HistoryData:
			logger.error(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			raise TypeError(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			return

		if not args[1].hasOrbits():
			logger.error(f"History Data Source for {self} contains no data yet.")
			return

		if type(args[2]) is not earth_raycast_data.EarthRayCastData:
			logger.error(f"setSource() of {self} requires a {earth_raycast_data.EarthRayCastData} as args[2], not: {type(args[2])}")
			raise TypeError(f"setSource() of {self} requires a {earth_raycast_data.EarthRayCastData} as args[2], not: {type(args[2])}")
			return

		# store old sensor configs
		old_sc_config = self.data['sc_config']
		if old_sc_config:
			old_config_filestem = old_sc_config.filestem
			old_suite_names = list(old_sc_config.getSensorSuites().keys())
		else:
			old_config_filestem = None
			old_suite_names = []
		if self.data['history_src']:
			old_pointing_defined = self.data['history_src'].getConfigValue('is_pointing_defined')
		else:
			old_pointing_defined = False

		# assign data sources
		self.data['sc_config'] = args[0]
		self.data['name'] = self.data['sc_config'].name
		self.data['history_src'] = args[1]
		self.data['raycast_src'] = args[2]
		self.data['strings'] = [self.data['sc_config'].name]

		first_sat_orbit = list(self.data['history_src'].getOrbits().values())[0]

		if hasattr(first_sat_orbit,'pos'):
			self.data['coords'] = np.hstack((first_sat_orbit.lon.reshape(-1,1),first_sat_orbit.lat.reshape(-1,1)))
			lat = ((first_sat_orbit.lat + 90) * self.data['vert_pixel_scale']).reshape(-1,1)
			lon = ((first_sat_orbit.lon + 180) * self.data['horiz_pixel_scale']).reshape(-1,1)
			self.data['scaled_coords'] = np.hstack((lon,lat))
			logger.debug(f'Setting source:coordinates for {self}')
		else:
			console.sendErr('Orbit has no position data')
			logger.warning(f'Orbit has no position data')
			raise ValueError('Orbit has no position data')

		if hasattr(first_sat_orbit,'name'):
			self.data['strings'] = [first_sat_orbit.name]
		else:
			self.data['strings'] = ['']

		if old_pointing_defined and self.data['sc_config'] == old_sc_config:
			# config has not changed -> don't need to re-instantiate sensors
			logger.debug('Spacecraft pointing related config has not changed')
			config_changed = False
			return

		# remove old sensors if there were some
		if old_pointing_defined and old_sc_config != self.data['sc_config']:
			# If pointing had previously been defined -> old sensors, options need to be removed
			# if no pointing, no point having sensors
			self._removeSensorAssets(old_suite_names)

		if self.data['history_src'].getConfigValue('is_pointing_defined'):
			self._instantiateSensorAssets()
			self._setSensorAssetSources()

	def setScale(self, horizontal_size, vertical_size):
		self.data['horiz_pixel_scale'] = horizontal_size/360
		self.data['vert_pixel_scale'] = vertical_size/180
		for asset in self.assets.values():
			asset.setScale(horizontal_size, vertical_size)

	def _instantiateAssets(self) -> None:
		if self.data['sc_config'] is not None:
			self._instantiateSensorAssets()

	def _removeSensorAssets(self, old_suite_names:list[str]) -> None:
		for suite_name in old_suite_names:
			self.assets[f'sensor_suite_{suite_name}'].removePlotOptions()
			self.assets[f'sensor_suite_{suite_name}'].detachFromParentViewRecursive()
			del(self.assets[f'sensor_suite_{suite_name}'])

	def _instantiateSensorAssets(self) -> None:
		for key, value in self.data['sc_config'].getSensorSuites().items():
			logger.info(f'Creating sensor suite sensor_suite_{key}')
			self.assets[f'sensor_suite_{key}'] = sensors.SensorSuite2DAsset(value,
																	name=key,
													 				v_parent=self.data['v_parent'])
	def _setSensorAssetSources(self) -> None:
		for asset_name, asset in self.assets.items():
			if 'sensor_suite_' in asset_name:
				asset.setSource(self.data['raycast_src'])

	def _createVisuals(self) -> None:
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
												 		antialias=0)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,2),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['spacecraft_marker_colour']['value']),
										edge_color='white',
										size=self.opts['spacecraft_marker_size']['value'],
										symbol='o')
		self.visuals['marker'].order = -20

	def getSensorSuiteByKey(self, sens_suite_key:str) -> sensors.SensorSuiteImageAsset:
		# key = self.data['sc_config'].values()[sens_suite_id]
		return self.assets[f'sensor_suite_{sens_suite_key}']

	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			self._updateMarkers()
			if self.data['history_src'].getConfigValue('is_pointing_defined'):
				pointing_data = self.data['history_src'].getPointings()[self.data['sc_config'].id]
				orbit_data = self.data['history_src'].getOrbits()[self.data['sc_config'].id]
				# set gizmo and sensor orientations
				#TODO: This check for last/next good pointing could be done better
				if np.any(np.isnan(pointing_data[self.data['curr_index'],:])):
					non_nan_found = False
					# look forwards
					for ii in range(self.data['curr_index'], len(pointing_data)):
						if np.all(np.isnan(pointing_data[ii,:])==False):
							non_nan_found = True
							quat = pointing_data[ii,:].reshape(-1,4)
							rotation = Rotation.from_quat(quat).as_matrix()
							break
						else:
							rotation = np.eye(3)
					if not non_nan_found:
						# look backwards
						for ii in range(self.data['curr_index'], -1, -1):
							if np.all(np.isnan(pointing_data[ii,:])==False):
								quat = pointing_data[ii,:].reshape(-1,4)
								rotation = Rotation.from_quat(quat).as_matrix()
								break
							else:
								rotation = np.eye(3)
				else:
					quat = pointing_data[self.data['curr_index']].reshape(-1,4)
					if self.data['history_src'].getConfigValue('pointing_invert_transform'):
						# Quat = ECI->BF
						rotation = Rotation.from_quat(quat).as_matrix()
					else:
						# Quat = BF->ECI
						rotation = Rotation.from_quat(quat).inv().as_matrix()
				for asset_name, asset in self.assets.items():
					if 'sensor_suite_' in asset_name:
						asset.setCurrentDatetime(self.data['history_src'].timespan[self.data['curr_index']])
				# recomputeRedraw child assets
				self.data['curr_pos'] = orbit_data.pos[self.data['curr_index']].reshape(1,3)
				self.data['curr_quat'] = quat
				self._recomputeRedrawChildren(pos=orbit_data.pos[self.data['curr_index']].reshape(1,3), rotation=rotation)
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		curr_world_pos = (self.data['coords'][self.data['curr_index']]).reshape(1,2)
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(None, None)]
		mo_info['world_pos'] = [curr_world_pos.reshape(2,)]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]
		return mo_info
		# return [(canvas_pos[0,0], canvas_pos[0,1])], ['SpIRIT']

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['spacecraft_marker_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMarkerColour,
											'widget_data': None}
		self._dflt_opts['plot_spacecraft_marker'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalMarkerVisibility,
											'widget_data': None}
		self._dflt_opts['spacecraft_marker_size'] = {'value': 15,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setOrbitalMarkerSize,
												'widget_data':None}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setMarkerColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['spacecraft_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setOrbitalMarkerSize(self, value:int) -> None:
		self.opts['spacecraft_marker_size']['value'] = value
		self._updateMarkers()

	def setOrbitalMarkerVisibility(self, state:bool) -> None:
		self.opts['plot_spacecraft_marker']['value'] = state
		self.visuals['marker'].visible = self.opts['plot_spacecraft_marker']['value']

	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'][self.data['curr_index']].reshape(1,2),
								   			size=self.opts['spacecraft_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['spacecraft_marker_colour']['value']))

	#----- HELPER FUNCTIONS -----#

class SpacecraftViewsAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()

		self.data['pointing_defined'] = False

		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Spacecraft'
		self.data['strings'] = ['']
		self.data['sens_suites'] = {}
		self.data['curr_index'] = 2
		self.data['sc_config'] = None
		self.data['history'] = None
		self.data['raycast_src'] = None

	def setSource(self, *args, **kwargs) -> None:
		# args[0] spacecraft configuration
		# args[1] history data
		# args[2] ray cast src data

		if type(args[0]) is not data_types.SpacecraftConfig:
			logger.error(f"setSource() of {self} requires a {data_types.SpacecraftConfig} as args[0], not: {type(args[0])}")
			raise TypeError(f"setSource() of {self} requires a {data_types.SpacecraftConfig} as args[0], not: {type(args[0])}")
			return

		if type(args[1]) is not history_data.HistoryData:
			logger.error(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			raise TypeError(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			return

		if not args[1].hasOrbits():
			logger.error(f"History Data Source for {self} contains no data yet.")
			return

		if type(args[2]) is not earth_raycast_data.EarthRayCastData:
			logger.error(f"setSource() of {self} requires a {earth_raycast_data.EarthRayCastData} as args[2], not: {type(args[2])}")
			raise TypeError(f"setSource() of {self} requires a {earth_raycast_data.EarthRayCastData} as args[2], not: {type(args[2])}")
			return

		# store old sensor configs
		old_sc_config = self.data['sc_config']
		if old_sc_config:
			old_config_filestem = old_sc_config.filestem
			old_suite_names = list(old_sc_config.getSensorSuites().keys())
		else:
			old_config_filestem = None
			old_suite_names = []
		if self.data['history']:
			old_pointing_defined = self.data['history'].getConfigValue('is_pointing_defined')
		else:
			old_pointing_defined = False

		# assign data sources
		self.data['sc_config'] = args[0]
		self.data['name'] = self.data['sc_config'].name
		self.data['history'] = args[1]
		self.data['raycast_src'] = args[2]
		self.data['strings'] = [self.data['sc_config'].name]

		if old_pointing_defined and self.data['sc_config'] == old_sc_config:
			# config has not changed -> don't need to re-instantiate sensors
			logger.debug('Spacecraft pointing related config has not changed')
			config_changed = False
			return

		# remove old sensors if there were some
		if old_pointing_defined and old_sc_config != self.data['sc_config']:
			# If pointing had previously been defined -> old sensors, options need to be removed
			# if no pointing, no point having sensors
			self._removeSensorAssets(old_suite_names)

		if self.data['history'].getConfigValue('is_pointing_defined'):
			self._instantiateSensorAssets()
			self._setSensorAssetSources()

	def _instantiateAssets(self) -> None:
		if self.data['sc_config'] is not None:
			self._instantiateSensorAssets()

	def _removeSensorAssets(self, old_suite_names:list[str]) -> None:
		for suite_name in old_suite_names:
			self.assets[f'sensor_suite_{suite_name}'].removePlotOptions()
			self.assets[f'sensor_suite_{suite_name}'].detachFromParentViewRecursive()
			del(self.assets[f'sensor_suite_{suite_name}'])

	def _instantiateSensorAssets(self) -> None:
		for key, value in self.data['sc_config'].getSensorSuites().items():
			logger.info(f'Creating sensor suite sensor_suite_{key}')
			self.assets[f'sensor_suite_{key}'] = sensors.SensorSuiteImageAsset(value,
																	name=key,
													 				v_parent=self.data['v_parent'])
	def _setSensorAssetSources(self) -> None:
		for asset_name, asset in self.assets.items():
			if 'sensor_suite_' in asset_name:
				asset.setSource(self.data['raycast_src'])

	def _createVisuals(self) -> None:
		pass

	def getSensorSuiteByKey(self, sens_suite_key:str) -> sensors.SensorSuiteImageAsset:
		# key = self.data['sc_config'].values()[sens_suite_id]
		return self.assets[f'sensor_suite_{sens_suite_key}']

	# Use AbstractAsset.updateIndex()

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			if self.data['history'].getConfigValue('is_pointing_defined'):
				pointing_data = self.data['history'].getPointings()[self.data['sc_config'].id]
				orbit_data = self.data['history'].getOrbits()[self.data['sc_config'].id]
				# set gizmo and sensor orientations
				#TODO: This check for last/next good pointing could be done better
				if np.any(np.isnan(pointing_data[self.data['curr_index'],:])):
					non_nan_found = False
					# look forwards
					for ii in range(self.data['curr_index'], len(pointing_data)):
						if np.all(np.isnan(pointing_data[ii,:])==False):
							non_nan_found = True
							quat = pointing_data[ii,:].reshape(-1,4)
							rotation = Rotation.from_quat(quat).as_matrix()
							break
						else:
							rotation = np.eye(3)
					if not non_nan_found:
						# look backwards
						for ii in range(self.data['curr_index'], -1, -1):
							if np.all(np.isnan(pointing_data[ii,:])==False):
								quat = pointing_data[ii,:].reshape(-1,4)
								rotation = Rotation.from_quat(quat).as_matrix()
								break
							else:
								rotation = np.eye(3)
				else:
					quat = pointing_data[self.data['curr_index']].reshape(-1,4)
					if self.data['history'].getConfigValue('pointing_invert_transform'):
						# Quat = ECI->BF
						rotation = Rotation.from_quat(quat).as_matrix()
					else:
						# Quat = BF->ECI
						rotation = Rotation.from_quat(quat).inv().as_matrix()
				for asset_name, asset in self.assets.items():
					if 'sensor_suite_' in asset_name:
						asset.setCurrentDatetime(self.data['history'].timespan[self.data['curr_index']])
						asset.setCurrentSunECI(orbit_data.sun_pos[self.data['curr_index']])
						asset.setCurrentMoonECI(orbit_data.moon_pos[self.data['curr_index']])
				# recomputeRedraw child assets
				self.data['curr_pos'] = orbit_data.pos[self.data['curr_index']].reshape(1,3)
				self.data['curr_quat'] = quat
				self._recomputeRedrawChildren(pos=orbit_data.pos[self.data['curr_index']].reshape(1,3), rotation=rotation)
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		pass
		# return [(canvas_pos[0,0], canvas_pos[0,1])], ['SpIRIT']

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	#----- HELPER FUNCTIONS -----#
