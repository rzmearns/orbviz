import logging
import numpy as np
from typing import Any
from vispy import scene
from vispy.scene.widgets.viewbox import ViewBox

import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours
import satplot.visualiser.interface.console as console
import spherapy.orbit as orbit

logger = logging.getLogger(__name__)

class Orbit3DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self._attachToParentView()
	
	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Primary Orbit'
		self.data['past'] = None
		self.data['future'] = None
		self.data['past_coords'] = None
		self.data['future_coords'] = None
		self.data['future_conn'] = None
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self._sliceData()

	def setSource(self, *args, **kwargs) -> None:
		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]
		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error(f"setSource() of {self} requires an {orbit.Orbit} as value of dict from args[0], not: {first_sat_orbit}")
			raise TypeError
		if hasattr(first_sat_orbit,'pos'):
			self.data['coords'] = first_sat_orbit.pos
			logger.debug(f'Setting source:coordinates for {self}')
		else:
			console.sendErr('Orbit has no position data')
			logger.warning(f'Orbit has no position data')
			raise ValueError('Orbit has no position data')

	def _instantiateAssets(self) -> None:
		# no sub assets
		pass
		
	def _createVisuals(self) -> None:
		self.visuals['past'] = scene.visuals.Line(self.data['past_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=True,
													width = self.opts['orbital_path_width']['value'],
													parent=None)
		self.visuals['future'] = scene.visuals.Line(self.data['future_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=True,
													width = self.opts['orbital_path_width']['value'],
													parent=None)

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index:int) -> None:
		self.data['curr_index'] = index
		self.setStaleFlagRecursive()
		self._sliceData()
		self._updateIndexChildren(index)

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			self.visuals['past'].set_data(pos=self.data['past_coords'])
			self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'])

			# recomputeRedraw child assets
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['plot_orbit'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['orbital_path_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setOrbitColour,
											'widget_data': None}
		self._dflt_opts['orbital_path_width'] = {'value': 1,
												'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathWidth,
											'widget_data': None}
		self._dflt_opts['orbital_path_past_style'] = {'value': 'solid',
												'type': 'option',
												'options': ['dash', 'solid'],
												'help': '',
												'static': True,
												'callback': None,
											'widget_data': None}
		self._dflt_opts['orbital_path_future_style'] = {'value': 'solid',
												'type': 'option',
												'options': ['dash', 'solid'],
												'help': '',
												'static': True,
												'callback': None,
											'widget_data': None}
		self._dflt_opts['plot_orbital_path_future'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathFutureVisibility,
											'widget_data': None}
		self._dflt_opts['plot_orbital_path_past'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathPastVisibility,
											'widget_data': None}
		self._dflt_opts['orbital_path_future_dash_size'] = {'value': 3,
										  		'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setFutureDashSize,
											'widget_data': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setOrbitColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['orbital_path_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['past'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['future'].set_data(color=colours.normaliseColour(new_colour))

	def setFutureDashSize(self, value:int) -> None:
		self.opts['orbital_path_future_dash_size']['value'] = value
		self.updateIndex(self.data['curr_index'])
		self.recomputeRedraw()

	def setOrbitalPathWidth(self, value:int) -> None:
		self.opts['orbital_path_width']['value'] = value
		self.visuals['past'].set_data(pos=self.data['past_coords'], width=value)
		self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'], width=value)

	def setOrbitalPathFutureVisibility(self, state:bool) -> None:
		self.opts['plot_orbital_path_future']['value'] = state
		self.visuals['future'].visible = self.opts['plot_orbital_path_future']['value']

	def setOrbitalPathPastVisibility(self, state:bool) -> None:
		self.opts['plot_orbital_path_past']['value'] = state
		self.visuals['past'].visible = self.opts['plot_orbital_path_past']['value']

	

	#----- HELPER FUNCTIONS -----#
	def _sliceData(self) -> None:
		self.data['past_coords'] = self.data['coords'][:self.data['curr_index']]
		self.data['future_coords'] = self.data['coords'][self.data['curr_index']:]

		coords_len = len(self.data['coords'])
		dash_size = self.opts['orbital_path_future_dash_size']['value']
		padded_len = coords_len - coords_len%(2*dash_size)

		conn = np.arange(padded_len-1,-1,-1).reshape(-1,dash_size*2)[:,:dash_size].reshape(1,-1)[0]
		conn = conn[np.where(conn > self.data['curr_index'])]
		self.data['future_conn'] = np.vstack((conn,conn-1)).T - self.data['curr_index']


class Orbit2DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Primary Orbit'
		self.data['past'] = None
		self.data['future'] = None
		self.data['trans_idx'] = None
		self.data['past_coords'] = None
		self.data['past_conn'] = None
		self.data['future_coords'] = None
		self.data['future_conn'] = None
		self.data['coords'] = np.zeros((4,2))
		self.data['scaled_coords'] = np.zeros((4,2))
		self.data['curr_index'] = 2
		self._findLongitudinalTransitions()
		self._sliceData()

	def setSource(self, *args, **kwargs) -> None:
		print(f'setting orbit source')
		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]
		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error(f"setSource() of {self} requires an {orbit.Orbit} as value of dict from args[0], not: {first_sat_orbit}")
			raise TypeError
		if hasattr(first_sat_orbit,'pos'):
			self.data['coords'] = np.hstack((first_sat_orbit.lon.reshape(-1,1),first_sat_orbit.lat.reshape(-1,1)))
			lat = ((first_sat_orbit.lat + 90) * self.data['vert_pixel_scale']).reshape(-1,1)
			lon = ((first_sat_orbit.lon + 180) * self.data['horiz_pixel_scale']).reshape(-1,1)
			self.data['scaled_coords'] = np.hstack((lon,lat))
			self._findLongitudinalTransitions()
			logger.debug(f'Setting source:coordinates for {self}')
		else:
			console.sendErr('Orbit has no position data')
			logger.warning(f'Orbit has no position data')
			raise ValueError('Orbit has no position data')

		if hasattr(first_sat_orbit,'name'):
			self.data['strings'] = [first_sat_orbit.name]
		else:
			self.data['strings'] = ['']

	def setScale(self, horizontal_size, vertical_size):
		self.data['horiz_pixel_scale'] = horizontal_size/360
		self.data['vert_pixel_scale'] = vertical_size/180
		print(f"{self.data['horiz_pixel_scale']=},{self.data['vert_pixel_scale']}")

	def _instantiateAssets(self) -> None:
		# no sub assets
		pass

	def _createVisuals(self) -> None:
		self.visuals['past'] = scene.visuals.Line(self.data['past_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=False,
													width = self.opts['orbital_path_width']['value'],
													parent=None)
		self.visuals['past'].antialias=1
		self.visuals['future'] = scene.visuals.Line(self.data['future_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=True,
													width = self.opts['orbital_path_width']['value'],
													parent=None)
		self.visuals['future'].antialias=1
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

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index:int) -> None:
		self.data['curr_index'] = index
		self.setStaleFlagRecursive()
		self._sliceData()
		self._updateIndexChildren(index)

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			self._updateMarkers()
			self.visuals['past'].set_data(pos=self.data['past_coords'], connect=self.data['past_conn'])
			self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'])
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		curr_world_pos = (self.data['coords'][self.data['curr_index']]).reshape(1,2)
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(None, None)]
		mo_info['world_pos'] = [curr_world_pos.reshape(2,)]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]
		return mo_info

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['plot_orbit'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['orbital_path_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setOrbitColour,
											'widget_data': None}
		self._dflt_opts['orbital_path_width'] = {'value': 1.5,
												'type': 'float',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathWidth,
											'widget_data': None}
		self._dflt_opts['orbital_path_past_style'] = {'value': 'solid',
												'type': 'option',
												'options': ['dash', 'solid'],
												'help': '',
												'static': True,
												'callback': None,
											'widget_data': None}
		self._dflt_opts['orbital_path_future_style'] = {'value': 'solid',
												'type': 'option',
												'options': ['dash', 'solid'],
												'help': '',
												'static': True,
												'callback': None,
											'widget_data': None}
		self._dflt_opts['plot_orbital_path_future'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathFutureVisibility,
											'widget_data': None}
		self._dflt_opts['plot_orbital_path_past'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathPastVisibility,
											'widget_data': None}
		self._dflt_opts['orbital_path_future_dash_size'] = {'value': 3,
										  		'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setFutureDashSize,
											'widget_data': None}
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
	def setOrbitColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['orbital_path_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['past'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['future'].set_data(color=colours.normaliseColour(new_colour))

	def setFutureDashSize(self, value:int) -> None:
		self.opts['orbital_path_future_dash_size']['value'] = value
		self.updateIndex(self.data['curr_index'])
		self.recomputeRedraw()

	def setOrbitalPathWidth(self, value:int) -> None:
		self.opts['orbital_path_width']['value'] = value
		self.visuals['past'].set_data(pos=self.data['past_coords'], connect=self.data['past_conn'], width=value)
		self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'], width=value)

	def setOrbitalPathFutureVisibility(self, state:bool) -> None:
		self.opts['plot_orbital_path_future']['value'] = state
		self.visuals['future'].visible = self.opts['plot_orbital_path_future']['value']

	def setOrbitalPathPastVisibility(self, state:bool) -> None:
		self.opts['plot_orbital_path_past']['value'] = state
		self.visuals['past'].visible = self.opts['plot_orbital_path_past']['value']

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

	def _findLongitudinalTransitions(self) -> None:
		self.data['trans_idx'] = np.where(np.abs(np.diff(self.data['coords'][:,0]))>300)[0]
		print(f"{self.data['trans_idx']=}")

	#----- HELPER FUNCTIONS -----#
	def _sliceData(self) -> None:
		self.data['past_coords'] = self.data['scaled_coords'][:self.data['curr_index']]
		self.data['future_coords'] = self.data['scaled_coords'][self.data['curr_index']:]
		self.data['future_unscaled_coords'] = self.data['coords'][self.data['curr_index']:]

		coords_len = len(self.data['coords'])
		dash_size = self.opts['orbital_path_future_dash_size']['value']
		padded_len = coords_len - coords_len%(2*dash_size)

		conn = np.arange(padded_len-1,-1,-1).reshape(-1,dash_size*2)[:,:dash_size].reshape(1,-1)[0]
		conn = conn[np.where(conn > self.data['curr_index'])]
		conn = conn[~np.isin(conn, self.data['trans_idx']+1)]
		self.data['future_conn'] = np.vstack((conn,conn-1)).T - self.data['curr_index']

		conn = np.arange(0,len(self.data['past_coords'])-1,1)
		conn = conn[~np.isin(conn, self.data['trans_idx'])]
		self.data['past_conn'] = np.vstack((conn,conn+1)).T