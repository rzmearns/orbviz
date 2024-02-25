import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons

import satplot.visualiser.controls.console as console


import geopandas as gpd

from vispy import scene, color

import numpy as np

class OrbitVisualiser(BaseAsset):
	def __init__(self, canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.requires_recompute = False
		self._setDefaultOptions()	
		self._initDummyData()
		self.draw()
	
	def draw(self):
		self.addOrbitalMarker()
		self.addOrbitalPath()

	def compute(self):
		pass

	def _initDummyData(self):
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 2
		self.sliceData()
		

	def sliceData(self):
		self.data['past_coords'] = self.data['coords'][:self.data['curr_index']]
		self.data['future_coords'] = self.data['coords'][self.data['curr_index']:]
		future_len = len(self.data['future_coords'])
		dash_size = self.opts['orbital_path_future_dash_size']['value']
		padded_future_len = padded_future_len = future_len - future_len%(2*dash_size)
		conn_picker = np.arange(padded_future_len).reshape(-1,dash_size*2)[:,:dash_size].reshape(1,-1)[0]
		conn_picker[np.where(conn_picker < future_len)]
		self.data['future_conn'] = np.array([np.arange(future_len-1),np.arange(1,future_len)]).T[conn_picker]

	def setSource(self, source):
		self.data['coords'] = source.pos

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.sliceData()
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.requires_recompute:
			self.visuals['past'].set_data(pos=self.data['past_coords'])
			self.visuals['future'].set_data(pos=self.data['future_coords'], connect=self.data['future_conn'])
			self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								   			size=self.opts['orbital_position_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']))

			self.requires_recompute = False

	def addOrbitalPath(self):
		self.visuals['past'] = scene.visuals.Line(self.data['past_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=self.opts['antialias']['value'],
													# connect=conn,
													parent=self.parent)
		self.visuals['future'] = scene.visuals.Line(self.data['future_coords'],
													color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
													antialias=self.opts['antialias']['value'],
													# connect=conn,
													parent=self.parent)

	def addOrbitalMarker(self):
		self.visuals['marker'] = scene.visuals.Markers(parent=self.parent, scaling=True, antialias=0)
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index']].reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
										edge_color='white',
										# edge_width=0,
										size=self.opts['orbital_position_marker_size']['value'],
										symbol='o')
														# size=10,
														# antialias=self.opts['antialias']['value'],
	   													# face_color=colours.normaliseColour(self.opts['orbital_path_colour']['value']),
														# edge_color='white',
														# edge_width=0,
														# scaling=True,
														# spherical=True,
														# parent=self.parent)

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_orbit'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setOrbitAssetVisibility}		
		self._dflt_opts['orbital_length'] = {'value': 1,
											'type': 'number',
											'help': '',
											'callback': None}
		self._dflt_opts['orbital_path_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'callback': self.setPrimOrbitColour}
		self._dflt_opts['orbital_path_width'] = {'value': 1,
											'type': 'number',
											'help': '',
											'callback': None}
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
										  		'type': 'number',
												'help': '',
												'callback': None}
		self._dflt_opts['orbital_path_future_dash_size'] = {'value': 3,
										  		'type': 'number',
												'help': '',
												'callback': None}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass
	
	def setPrimOrbitColour(self, new_colour):
		self.opts['orbital_path_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['past'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['future'].set_data(color=colours.normaliseColour(new_colour))
		self.visuals['marker'].set_data(face_color=colours.normaliseColour(new_colour))

	def setOrbitAssetVisibility(self, state):
		self.setOrbitalPathFutureVisibility(state)
		self.setOrbitalPathFutureVisibility(state)
		self.setOrbitalMarkerVisibility(state)

	def setOrbitalPathFutureVisibility(self, state):
		self.visuals['future'].visible = state

	def setOrbitalPathPastVisibility(self, state):
		self.visuals['past'].visible = state

	def setOrbitalMarkerVisibility(self, state):
		self.visuals['marker'].visible = state