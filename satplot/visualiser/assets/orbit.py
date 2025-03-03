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
			print(f'Setting source:coordinates for {self}')
		else:
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
		self._constructVisibilityStruct()

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
											'widget': None}
		self._dflt_opts['orbital_path_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setOrbitColour,
											'widget': None}
		self._dflt_opts['orbital_path_width'] = {'value': 1,
												'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathWidth,
											'widget': None}
		self._dflt_opts['orbital_path_past_style'] = {'value': 'solid',
												'type': 'option',
												'options': 'dash', 'solid'
												'help': '',
												'static': True,
												'callback': None,
											'widget': None}
		self._dflt_opts['orbital_path_future_style'] = {'value': 'solid',
												'type': 'option',
												'options': 'dash', 'solid'
												'help': '',
												'static': True,
												'callback': None,
											'widget': None}
		self._dflt_opts['plot_orbital_path_future'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathFutureVisibility,
											'widget': None}
		self._dflt_opts['plot_orbital_path_past'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOrbitalPathPastVisibility,
											'widget': None}
		self._dflt_opts['orbital_path_future_dash_size'] = {'value': 3,
										  		'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setFutureDashSize,
											'widget': None}

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
		self.visuals['future'].visible = state
		self._visuals_visibility['future'] = state
		

	def setOrbitalPathPastVisibility(self, state:bool) -> None:
		self.visuals['past'].visible = state
		self._visuals_visibility['past'] = state

	

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