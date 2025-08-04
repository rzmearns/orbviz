import logging

import typing
from typing import Any

import numpy as np

import vispy.scene as scene

from satplot.model.data_models import groundstation_data
import satplot.model.data_models.history_data as history_data
import satplot.model.geometry.spherical as spherical_geom
import satplot.util.constants as c
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours
import satplot.visualiser.visuals.polygons as polygon_visuals

logger = logging.getLogger(__name__)

class GroundStation3DAsset(base_assets.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Moon'
		self.data['coords'] = np.zeros((4,3))
		self.data['curr_index'] = 0

		self.data['strings'] = []

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		# Sun Sphere
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
														antialias=0,
														spherical=True)
		self.visuals['marker'].set_data(pos=self.data['coords'],
										edge_width=0,
										face_color=colours.normaliseColour(self.opts['groundstation_marker_colour']['value']),
										edge_color='white',
										size=self.opts['groundstation_marker_size']['value'])
		self.visuals['marker'].order = -1


	def setSource(self, *args, **kwargs):
		# args[0] groundstation data
		# args[1] history data
		if type(args[0]) is not groundstation_data.GroundStationCollection:
			logger.error("setSource() of %s requires a %s as args[1], not: {type(args[1])}", self, groundstation_data.GroundStationCollection)
			raise TypeError(f"setSource() of {self} requires a {groundstation_data.GroundStationCollection} as args[1], not: {type(args[1])}")

		self.data['groundstations'] = args[0]
		stations = self.data['groundstations'].getStations()
		num_stations = len(stations.values())
		num_tstamps = len(list(stations.values())[0].eci)
		self.data['coords'] = np.zeros((num_tstamps, num_stations, 3))
		self.data['strings'] = []
		for ii, station in enumerate(stations.values()):
			self.data['coords'][:,ii,:] = station.eci
			self.data['strings'].append(station.name)

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index):
		self.setStaleFlagRecursive()
		self.data['curr_index'] = index
		self._updateIndexChildren(index)

	def recomputeRedraw(self):
		if self.isFirstDraw():
			self._detachFromParentView()
			self._attachToParentView()

			self._clearFirstDrawFlag()
		if self.isStale():
			# move the moon
			self._updateMarkers()
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		curr_world_pos = (self.data['coords'][self.data['curr_index'],:,:])
		canvas_pos = self.visuals['marker'].get_transform('visual','canvas').map(curr_world_pos)
		canvas_pos /= canvas_pos[:,3:]
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(canvas_pos[ii,0], canvas_pos[ii,1]) for ii in range(len(self.data['coords'][self.data['curr_index'],:,:]))]
		mo_info['world_pos'] = [self.data['coords'][self.data['curr_index'],ii,:].reshape(3,) for ii in range(len(self.data['coords'][self.data['curr_index'],:,:]))]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self for ii in range(len(self.data['coords']))]
		return mo_info

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['plot_groundstations'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['groundstation_marker_colour'] = {'value': (243,243,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGroundStationMarkerColour,
											'widget_data': None}
		self._dflt_opts['groundstation_marker_size'] = {'value': 300,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGroundStationMarkerSize,
											'widget_data': None}
		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['coords'][self.data['curr_index'],:,:].reshape(-1,3),
											size=self.opts['groundstation_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['groundstation_marker_colour']['value']))

	def setGroundStationMarkerColour(self, new_colour):
		logger.debug("Changing GroundStation marker colour %s -> %s", self.opts['groundstation_marker_colour']['value'], new_colour)
		self.opts['groundstation_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setGroundStationMarkerSize(self, size):
		logger.debug("Changing ground station marker size %s -> %s", self.opts['groundstation_marker_size']['value'], size)
		self.opts['groundstation_marker_size']['value'] = size
		self._updateMarkers()

	def setMarkerStyle(self, option_idx):
		new_style = self.opts['groundstation_marker_style']['options'][option_idx]
		logger.debug("Changing groundstation marker style %s -> %s", self.opts['groundstation_marker_style']['value'], new_style)
		self.opts['groundstation_marker_style']['value'] = new_style
		self._updateMarkers()


class GroundStation2DAsset(base_assets.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Moon'
		self.data['coords'] = np.zeros((4,2))
		self.data['scaled_coords'] = np.zeros((4,2))
		self.data['curr_index'] = 0

		self.data['strings'] = []

		self.data['oth_edge1'] = -1*np.ones((364,2))
		# need to create a valid polygon for instantiation (but before valid data exists)
		self.data['oth_edge1'][:363,0] = np.arange(0,363)
		self.data['oth_edge1'][-1,1] = -1
		self.data['oth_edge1'][-2,1] = -2
		self.data['oth_edge2'] = self.data['oth_edge1'].copy()

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		# Sun Sphere
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
														antialias=0)
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'],
										edge_width=0,
										face_color=colours.normaliseColour(self.opts['groundstation_marker_colour']['value']),
										edge_color='white',
										size=self.opts['groundstation_marker_size']['value'],
										symbol=self.opts['groundstation_marker_style']['value'])
		self.visuals['marker'].order = -1

	def _recreateOTHCircleVisuals(self):
		if 'oth_circles1' in self.visuals.keys():
			for visual in self.visuals['oth_circles1']:
				visual.parent=None
			del self.visuals['oth_circles1']

		if 'oth_circles2' in self.visuals.keys():
			for visual in self.visuals['oth_circles2']:
				visual.parent=None
			del self.visuals['oth_circles2']

		self.visuals['oth_circles1'] = []
		self.visuals['oth_circles2'] = []
		for ii in range(len(self.data['oth_edges1'])):
			v = polygon_visuals.FastPolygon(self.data['oth_edges1'][ii],
												color=colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value']),
												border_color=colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value']),
												border_width=2,
												parent=None)
			v.opacity = self.opts['over_the_horizon_circle_alpha']['value']
			v.order = 1
			v.set_gl_state('translucent', depth_test=False)
			self.visuals['oth_circles1'].append(v)
			v2 = polygon_visuals.FastPolygon(self.data['oth_edges2'][ii],
												color=colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value']),
												border_color=colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value']),
												border_width=2,
												parent=None)
			v2.opacity = self.opts['over_the_horizon_circle_alpha']['value']
			v2.order = 1
			v2.set_gl_state('translucent', depth_test=False)
			self.visuals['oth_circles2'].append(v2)

	def setSource(self, *args, **kwargs):
		# args[0] groundstation data
		if type(args[0]) is not groundstation_data.GroundStationCollection:
			logger.error("setSource() of %s requires a %s as args[1], not: {type(args[1])}", self, groundstation_data.GroundStationCollection)
			raise TypeError(f"setSource() of {self} requires a {groundstation_data.GroundStationCollection} as args[1], not: {type(args[1])}")

		if type(args[1]) is not history_data.HistoryData:
			logger.error("setSource() of %s requires a %s as args[1], not: %s", self, history_data.HistoryData, type(args[1]))
			raise TypeError(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")

		self.data['groundstations'] = args[0]
		self.data['history_src'] = args[1]

		stations = self.data['groundstations'].getStations()
		num_stations = len(stations.values())
		self.data['coords'] = np.zeros((num_stations, 2))
		self.data['strings'] = []
		self.data['min_elevations'] = []
		self.data['oth_edges1'] = []
		self.data['oth_edges2'] = []
		self.data['oth_circle_splits'] = []
		for ii, station in enumerate(stations.values()):
			self.data['coords'][ii,0] = station.latlon[1] 	# longitude
			self.data['coords'][ii,1] = station.latlon[0] 	# latitude
			self.data['strings'].append(station.name)
			self.data['min_elevations'].append(station.min_elevation)

			edge1_data, edge2_data, split = self.calcOTHCircle(self.data['min_elevations'][ii], self.data['coords'][ii])
			self.data['oth_edges1'].append(edge1_data)
			self.data['oth_edges2'].append(edge2_data)
			self.data['oth_circle_splits'].append(split)

		self.data['scaled_coords'] = self._scale(self.data['coords'])

		self._recreateOTHCircleVisuals()
		for ii in range(len(stations.values())):
			if self.data['oth_circle_splits'][ii]:
				self.visuals['oth_circles1'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']
				self.visuals['oth_circles2'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']
			else:
				self.visuals['oth_circles1'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']/2
				self.visuals['oth_circles2'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']/2


	def setScale(self, horizontal_size, vertical_size):
		self.data['horiz_pixel_scale'] = horizontal_size/360
		self.data['vert_pixel_scale'] = vertical_size/180

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index):
		self.setStaleFlagRecursive()
		self.data['curr_index'] = index
		self._updateIndexChildren(index)

	def recomputeRedraw(self):
		if self.isFirstDraw():
			self._detachFromParentView()
			self._attachToParentView()

			self._clearFirstDrawFlag()
		if self.isStale():
			self._updateMarkers()
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(None, None) for _ in range(len(self.data['coords']))]
		mo_info['world_pos'] = [(self.data['coords'][ii,1],self.data['coords'][ii,0]) for ii in range(len(self.data['coords']))]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self for ii in range(len(self.data['coords']))]
		return mo_info

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['plot_groundstations'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['groundstation_marker_colour'] = {'value': (243,243,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGroundStationMarkerColour,
											'widget_data': None}
		self._dflt_opts['groundstation_marker_size'] = {'value': 20,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGroundStationMarkerSize,
											'widget_data': None}
		self._dflt_opts['groundstation_marker_style'] = {'value': 'disc',
												'type': 'option',
												'options':['disc','arrow','ring','clobber','square','x','diamond','vbar','hbar','cross','tailed_arrow','triangle_up','triangle_down','star','cross_lines'],
												'help': '',
												'static': True,
												'callback': self.setMarkerStyle,
											'widget_data': None}
		self._dflt_opts['plot_over_the_horizon_circle'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setOTHCircleVisibility,
											'widget_data': None}
		self._dflt_opts['over_the_horizon_circle_colour'] = {'value': (255,100,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setOTHCircleColour,
											'widget_data': None}
		self._dflt_opts['over_the_horizon_circle_alpha'] = {'value': 0.5,
												'type': 'fraction',
												'help': '',
												'static': True,
												'callback': self.setOTHCircleAlpha,
												'widget_data': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'],
											size=self.opts['groundstation_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['groundstation_marker_colour']['value']),
											symbol=self.opts['groundstation_marker_style']['value'])

	def setGroundStationMarkerColour(self, new_colour):
		logger.debug("Changing GroundStation marker colour %s -> %s", self.opts['groundstation_marker_colour']['value'], new_colour)
		self.opts['groundstation_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setGroundStationMarkerSize(self, size):
		logger.debug("Changing ground station marker size %s -> %s", self.opts['groundstation_marker_size']['value'], size)
		self.opts['groundstation_marker_size']['value'] = size
		self._updateMarkers()

	def setMarkerStyle(self, option_idx):
		new_style = self.opts['groundstation_marker_style']['options'][option_idx]
		logger.debug("Changing groundstation marker style %s -> %s", self.opts['groundstation_marker_style']['value'], new_style)
		self.opts['groundstation_marker_style']['value'] = new_style
		self._updateMarkers()

	def setOTHCircleAlpha(self, alpha):
		# Takes a little while to take effect.
		logger.debug("Changing groundstation OTH alpha %s -> %s",  self.opts['over_the_horizon_circle_alpha']['value'], alpha)
		self.opts['over_the_horizon_circle_alpha']['value'] = alpha
		for ii in range(len(self.visuals['oth_circles1'])):
			if self.data['oth_circle_splits'][ii]:
				self.visuals['oth_circles1'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']
				self.visuals['oth_circles2'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']
			else:
				self.visuals['oth_circles1'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']/2
				self.visuals['oth_circles2'][ii].opacity = self.opts['over_the_horizon_circle_alpha']['value']/2

	def setOTHCircleColour(self, new_colour):
		logger.debug("Changing groundstation OTH colour %s -> %s", self.opts['over_the_horizon_circle_colour']['value'], new_colour)
		self.opts['over_the_horizon_circle_colour']['value'] = new_colour
		for ii in range(len(self.visuals['oth_circles1'])):
			self.visuals['oth_circles1'][ii].color = colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value'])
			self.visuals['oth_circles2'][ii].color = colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value'])
			self.visuals['oth_circles1'][ii].border_color = colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value'])
			self.visuals['oth_circles2'][ii].border_color = colours.normaliseColour(self.opts['over_the_horizon_circle_colour']['value'])

	def setOTHCircleVisibility(self, state):
		self.opts['plot_over_the_horizon_circle']['value'] = state
		for ii in range(len(self.visuals['oth_circles1'])):
			self.visuals['oth_circles1'][ii].visible = self.opts['plot_over_the_horizon_circle']['value']
			self.visuals['oth_circles2'][ii].visible = self.opts['plot_over_the_horizon_circle']['value']

	def calcOTHCircle(self, min_elevation:float, center:np.ndarray[tuple[int],np.dtype[np.float64]]):
		prim_orbit = list(self.data['history_src'].getOrbits().values())[0]
		eci_pos = prim_orbit.pos[self.data['curr_index']]
		alt = np.linalg.norm(eci_pos)
		phi = np.rad2deg(self._calcCentralAngle(alt, min_elevation))
		lats, lons1, lons2 = spherical_geom.genSmallCircleCenterSubtendedAngle(phi*2, center[1], center[0])
		circle1, circle2 = spherical_geom.splitSmallCirclePatch(center[0], center[1], lats, lons1, lons2)

		if np.all(circle1 == circle2):
			split = False
		else:
			split = True

		return self._scale(circle1), self._scale(circle2), split

	def _calcCentralAngle(self, alt:float, min_elevation:float) -> float:
		central_el = np.deg2rad(min_elevation)+np.pi/2
		alpha = np.arcsin(c.R_EARTH*np.sin(central_el)/(alt))
		return np.pi-alpha-central_el

	def _scale(self, coords):
		out_arr = coords.copy()
		out_arr[:,0] = (out_arr[:,0] + 180) * self.data['horiz_pixel_scale']
		out_arr[:,1] = (out_arr[:,1] + 90) * self.data['vert_pixel_scale']
		return out_arr