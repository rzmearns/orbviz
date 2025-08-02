import logging

import typing
from typing import Any

import numpy as np
import pymap3d
import spherapy.orbit as orbit

import vispy.scene as scene
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.transforms as vtransforms

from satplot.model.data_models import event_data
import satplot.model.geometry.primgeom as pg
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours

logger = logging.getLogger(__name__)

class Moon3DAsset(base_assets.AbstractAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self._attachToParentView()
	
	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'Moon'		
		self.data['curr_pos'] = None
		self.data['pos'] = None

	def setSource(self, *args, **kwargs) -> None:
		if type(args[0]) is not orbit.Orbit:
			logger.error("setSource() of %s requires an %s as value of dict from args[0], not: {type(args[0])}", self, orbit.Orbit)
			raise TypeError
		self.data['pos'] = args[0].moon_pos

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['moon'] = scene.visuals.Sphere(radius=self.opts['moon_sphere_radius_kms']['value'],
												method='latitude',
												color=colours.normaliseColour(self.opts['moon_sphere_colour']['value']),
												parent=None)

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index:int) -> None:
		self.setStaleFlagRecursive()
		self.data['curr_index'] = index
		self.data['curr_pos'] = self.data['pos'][self.data['curr_index']]
		self._updateIndexChildren(index)

	def recomputeRedraw(self) -> None:
		if self.isFirstDraw():
			self._clearFirstDrawFlag()
		if self.isStale():
			moon_pos = self.opts['moon_distance_kms']['value'] * pg.unitVector(self.data['curr_pos'])
			self.visuals['moon'].transform = vtransforms.STTransform(translate=moon_pos)

			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	
	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}
		self._dflt_opts['plot_moon'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setMoonSphereVisibility,
											'widget_data': None}
		self._dflt_opts['moon_sphere_colour'] = {'value': (61,61,61),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMoonSphereColour,
											'widget_data': None}
		self._dflt_opts['moon_distance_kms'] = {'value': 15000,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setMoonDistance,
											'widget_data': None}
		self._dflt_opts['moon_sphere_radius_kms'] = {'value': 786,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setMoonSphereRadius,
											'widget_data': None}

		# moon radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()
	
	#----- OPTIONS CALLBACKS -----#
	def setMoonSphereColour(self, new_colour:tuple[float,float,float]) -> None:
		logger.debug("Changing moon sphere colour %s -> %s", self.opts['moon_sphere_colour']['value'], new_colour)
		self.opts['moon_sphere_colour']['value'] = new_colour
		n_faces = self.visuals['moon'].mesh._meshdata.n_faces
		n_verts = self.visuals['moon'].mesh._meshdata.n_vertices
		self.visuals['moon'].mesh._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['moon'].mesh._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['moon'].mesh.mesh_data_changed()

	def setAntialias(self, state:bool) -> None:
		raise NotImplementedError

	def setMoonDistance(self, distance:float) -> None:
		self.opts['moon_distance_kms']['value'] = distance
		# TODO: fix this to setStale then recomputeRedraw()
		self.setStaleFlagRecursive()
		self.recomputeRedraw()

	def setMoonSphereRadius(self, radius:float) -> None:
		self.opts['moon_sphere_radius_kms']['value'] = radius
		self.visuals['moon'].parent = None
		self._createVisuals()
		self.visuals['moon'].parent = self.data['v_parent']
		self.requires_recompute = True
		# TODO: fix this to setStale then recomputeRedraw()
		self.setStaleFlagRecursive()
		self.recomputeRedraw()

	def setMoonSphereVisibility(self, state:bool) -> None:
		self.opts['plot_moon']['value'] = state
		self.visuals['moon'].visible = self.opts['plot_moon']['value']

class Events2DAsset(base_assets.AbstractAsset):
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
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'][self.data['curr_index']].reshape(1,2),
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
			return

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
