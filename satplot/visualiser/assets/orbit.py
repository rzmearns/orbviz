import numpy as np
from typing import Any
from vispy import scene
from vispy.scene.widgets.viewbox import ViewBox

import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours
import spherapy.orbit as orbit


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
			raise TypeError
		if hasattr(first_sat_orbit,'pos'):
			self.data['coords'] = first_sat_orbit.pos
		else:
			raise ValueError('Orbit has no position data')
		if hasattr(first_sat_orbit,'name'):
			self.data['strings'] = [first_sat_orbit.name]
		else:
			self.data['strings'] = ['']

	def _instantiateAssets(self) -> None:
		# no sub assets
		pass
		
	def _createVisuals(self) -> None:
		self.visuals['past'] = scene.visuals.Line(self.data['past_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=self.opts['antialias']['value'],
													width = self.opts['orbital_path_width']['value'],
													parent=None)
		self.visuals['future'] = scene.visuals.Line(self.data['future_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=self.opts['antialias']['value'],
													width = self.opts['orbital_path_width']['value'],
													parent=None)

		self.visuals['marker'] = scene.visuals.Markers(parent=None,
												 		scaling=True,
														antialias=0)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
										edge_color='white',
										size=self.opts['orbital_position_marker_size']['value'],
										symbol='o')

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
			self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))

			# recomputeRedraw child assets
			self._recomputeRedrawChildren()
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


	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_orbit'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setVisibility}		
		self._dflt_opts['orbital_path_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'callback': self.setOrbitColour}
		self._dflt_opts['orbital_path_width'] = {'value': 1,
											'type': 'integer',
											'help': '',
											'callback': self.setOrbitalPathWidth}
		self._dflt_opts['orbital_path_past_style'] = {'value': 'solid',
												'type': 'option',
												'options': 'dash', 'solid'
												'help': '',
												'callback': None}
		self._dflt_opts['orbital_path_future_style'] = {'value': 'solid',
												'type': 'option',
												'options': 'dash', 'solid'
												'help': '',
												'callback': None}
		self._dflt_opts['plot_orbital_path_future'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalPathFutureVisibility}
		self._dflt_opts['plot_orbital_path_past'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalPathPastVisibility}
		self._dflt_opts['plot_orbital_position_marker'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitalMarkerVisibility}
		self._dflt_opts['orbital_position_marker_size'] = {'value': 500,
										  		'type': 'integer',
												'help': '',
												'callback': self.setOrbitalMarkerSize}
		self._dflt_opts['orbital_path_future_dash_size'] = {'value': 3,
										  		'type': 'integer',
												'help': '',
												'callback': self.setFutureDashSize}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def setOrbitColour(self, new_colour:tuple[float,float,float]) -> None:
		self.opts['orbital_path_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['past'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['future'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))

	def setOrbitalMarkerSize(self, value:int) -> None:
		self.opts['orbital_position_marker_size']['value'] = value
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))
		self.visuals['marker'].update()

	def setFutureDashSize(self, value:int) -> None:
		self.opts['orbital_path_future_dash_size']['value'] = value
		self.updateIndex(self.data['curr_index'])

	def setOrbitalPathWidth(self, value:int) -> None:
		self.opts['orbital_path_width']['value'] = value
		self.visuals['past'].set_data(pos=self.data['past_coords'], width=value)
		self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'], width=value)

	def setOrbitalPathFutureVisibility(self, state:bool) -> None:
		self.visuals['future'].visible = state
		

	def setOrbitalPathPastVisibility(self, state:bool) -> None:
		self.visuals['past'].visible = state

	def setOrbitalMarkerVisibility(self, state:bool) -> None:
		self.visuals['marker'].visible = state

	

	#----- HELPER FUNCTIONS -----#
	def _sliceData(self) -> None:
		self.data['past_coords'] = self.data['coords'][:self.data['curr_index']]
		self.data['future_coords'] = self.data['coords'][self.data['curr_index']:]
		future_len = len(self.data['future_coords'])
		dash_size = self.opts['orbital_path_future_dash_size']['value']
		padded_future_len = padded_future_len = future_len - future_len%(2*dash_size)
		conn_picker = np.arange(padded_future_len).reshape(-1,dash_size*2)[:,:dash_size].reshape(1,-1)[0]
		conn_picker[np.where(conn_picker < future_len)]
		self.data['future_conn'] = np.array([np.arange(future_len-1),np.arange(1,future_len)]).T[conn_picker]