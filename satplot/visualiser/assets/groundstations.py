import logging

import typing
from typing import Any

import numpy as np

import vispy.scene as scene

from satplot.model.data_models import groundstation_data
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours

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

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		# Sun Sphere
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
														antialias=0)
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'],
										edge_width=0,
										face_color=colours.normaliseColour(self.opts['prior_events_marker_colour']['value']),
										edge_color='white',
										size=self.opts['events_marker_size']['value'],
										symbol=self.opts['events_marker_style']['value'])
		self.visuals['marker'].order = -1


	def setSource(self, *args, **kwargs):
		# args[0] history data
		if type(args[0]) is not event_data.EventData:
			logger.error("setSource() of %s requires a %s as args[1], not: {type(args[1])}", self, event_data.EventData)
			raise TypeError(f"setSource() of {self} requires a {event_data.EventData} as args[1], not: {type(args[1])}")

		self.data['events_src'] = args[0]
		self.data['coords'] = self.data['events_src'].latlon

		scaled_lat = ((self.data['coords'][:,0] + 90) * self.data['vert_pixel_scale']).reshape(-1,1)
		scaled_lon = ((self.data['coords'][:,1] + 180) * self.data['horiz_pixel_scale']).reshape(-1,1)
		self.data['scaled_coords'] = np.hstack((scaled_lon,scaled_lat))

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
			# move the moon
			self._updateMarkers()
			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def getScreenMouseOverInfo(self) -> dict[str, Any]:
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(None, None) for _ in range(len(self.data['coords']))]
		mo_info['world_pos'] = [(self.data['coords'][ii,1],self.data['coords'][ii,0]) for ii in range(len(self.data['coords']))]
		mo_info['strings'] = self.data['events_src'].descriptions
		mo_info['objects'] = [self for ii in range(len(self.data['coords']))]
		return mo_info

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['plot_events'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['prior_events_marker_colour'] = {'value': (156,0,252),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setPriorEventsMarkerColour,
											'widget_data': None}
		self._dflt_opts['post_events_marker_colour'] = {'value': (80,60,125),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setPostEventsMarkerColour,
											'widget_data': None}
		self._dflt_opts['events_marker_size'] = {'value': 15,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setEventsMarkerSize,
											'widget_data': None}
		self._dflt_opts['events_marker_style'] = {'value': 'disc',
												'type': 'option',
												'options':['disc','arrow','ring','clobber','square','x','diamond','vbar','hbar','cross','tailed_arrow','triangle_up','triangle_down','star','cross_lines'],
												'help': '',
												'static': True,
												'callback': self.setMarkerStyle,
											'widget_data': None}
		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		cols = np.tile(colours.normaliseColour(self.opts['prior_events_marker_colour']['value']),(len(self.data['coords']),1))
		_, post_truth = self.data['events_src'].sliceByTimespanIdx(self.data['curr_index'])
		cols[post_truth] = colours.normaliseColour(self.opts['post_events_marker_colour']['value'])
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'].reshape(-1,2),
											size=self.opts['events_marker_size']['value'],
											face_color=cols,
											symbol=self.opts['events_marker_style']['value'])

	def setPriorEventsMarkerColour(self, new_colour):
		logger.debug("Changing events prior marker colour %s -> %s", self.opts['prior_events_marker_colour']['value'], new_colour)
		self.opts['prior_events_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setPostEventsMarkerColour(self, new_colour):
		logger.debug("Changing events post marker colour %s -> %s", self.opts['post_events_marker_colour']['value'], new_colour)
		self.opts['post_events_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setEventsMarkerSize(self, size):
		logger.debug("Changing events marker size %s -> %s", self.opts['events_marker_size']['value'], size)
		self.opts['events_marker_size']['value'] = size
		self._updateMarkers()

	def setMarkerStyle(self, option_idx):
		new_style = self.opts['events_marker_style']['options'][option_idx]
		logger.debug("Changing events marker style %s -> %s", self.opts['events_marker_style']['value'], new_style)
		self.opts['events_marker_style']['value'] = new_style
		self._updateMarkers()
