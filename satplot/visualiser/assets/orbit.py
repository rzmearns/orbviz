import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons
import spherapy.orbit as orbit

import satplot.visualiser.controls.console as console


import geopandas as gpd

from vispy import scene, color

import numpy as np

class OrbitVisualiser(BaseAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self.attachToParentView()
	
	def _initData(self):
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

	def setSource(self, *args, **kwargs):
		if type(args[0]) is not orbit.Orbit:
			raise TypeError
		if hasattr(args[0],'pos'):
			self.data['coords'] = args[0].pos
		else:
			raise ValueError('Orbit has no position data')
		if hasattr(args[0],'name'):
			self.data['strings'] = [args[0].name]
		else:
			self.data['strings'] = ['']

	def _instantiateAssets(self):
		# no sub assets
		pass
		
	def _createVisuals(self):
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

	# Override BaseAsset.updateIndex()
	def updateIndex(self, index):
		self.data['curr_index'] = index
		self._sliceData()
		for asset in self.assets.values():
			if isinstance(asset,BaseAsset):
				asset.updateIndex(index)
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.first_draw:
			self.first_draw = False
		if self.requires_recompute:
			self.visuals['past'].set_data(pos=self.data['past_coords'])
			self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'])
			self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))

			for asset in self.assets.values():
				asset.recompute()

			self.requires_recompute = False

	def getScreenMouseOverInfo(self):
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


	def _setDefaultOptions(self):
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
	def setOrbitColour(self, new_colour):
		self.opts['orbital_path_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['past'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['future'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))

	def setOrbitalMarkerSize(self, value):
		self.opts['orbital_position_marker_size']['value'] = value
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))
		self.visuals['marker'].update()

	def setFutureDashSize(self, value):
		self.opts['orbital_path_future_dash_size']['value'] = value
		self.updateIndex(self.data['curr_index'])

	def setOrbitalPathWidth(self, value):
		self.opts['orbital_path_width']['value'] = value
		self.visuals['past'].set_data(pos=self.data['past_coords'], width=value)
		self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'], width=value)

	def setOrbitalPathFutureVisibility(self, state):
		self.visuals['future'].visible = state
		

	def setOrbitalPathPastVisibility(self, state):
		self.visuals['past'].visible = state

	def setOrbitalMarkerVisibility(self, state):
		self.visuals['marker'].visible = state

	

	#----- HELPER FUNCTIONS -----#
	def _sliceData(self):
		self.data['past_coords'] = self.data['coords'][:self.data['curr_index']]
		self.data['future_coords'] = self.data['coords'][self.data['curr_index']:]
		future_len = len(self.data['future_coords'])
		dash_size = self.opts['orbital_path_future_dash_size']['value']
		padded_future_len = padded_future_len = future_len - future_len%(2*dash_size)
		conn_picker = np.arange(padded_future_len).reshape(-1,dash_size*2)[:,:dash_size].reshape(1,-1)[0]
		conn_picker[np.where(conn_picker < future_len)]
		self.data['future_conn'] = np.array([np.arange(future_len-1),np.arange(1,future_len)]).T[conn_picker]