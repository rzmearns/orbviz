import logging

from typing import Any

import numpy as np
import pymap3d
import spherapy.orbit as orbit

import vispy.scene as scene
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.transforms as vtransforms

import satplot.model.data_models.history_data as history_data
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

class Moon2DAsset(base_assets.AbstractAsset):
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

		self.data['strings'] = [self.data['name']]

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		# Sun Sphere
		self.visuals['marker'] = scene.visuals.Markers(parent=None,
														scaling=True,
														antialias=0)
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'][self.data['curr_index']].reshape(1,2),
										edge_width=0,
										face_color=colours.normaliseColour(self.opts['moon_marker_colour']['value']),
										edge_color='white',
										size=self.opts['moon_marker_size']['value'],
										symbol='o')
		self.visuals['marker'].order = -1


	def setSource(self, *args, **kwargs):
		# args[0] history data
		if type(args[0]) is not history_data.HistoryData:
			logger.error("setSource() of %s requires a %s as args[1], not: {type(args[1])}", self, history_data.HistoryData)
			raise TypeError(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			return

		self.data['history_src'] = args[0]
		first_sat_orbit = list(self.data['history_src'].getOrbits().values())[0]

		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error("data source for %s is not an orbit.Orbit, can't extract moon location data", self)
			raise TypeError

		lat, lon, alt = pymap3d.eci2geodetic(first_sat_orbit.moon_pos[:,0],
											first_sat_orbit.moon_pos[:,1],
											first_sat_orbit.moon_pos[:,2],
											first_sat_orbit.timespan.asDatetime())
		self.data['coords'] = np.vstack((lon,lat)).T
		scaled_lat = ((lat + 90) * self.data['vert_pixel_scale']).reshape(-1,1)
		scaled_lon = ((lon + 180) * self.data['horiz_pixel_scale']).reshape(-1,1)
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
		curr_world_pos = (self.data['coords'][self.data['curr_index']]).reshape(1,2)
		mo_info = {'screen_pos':[], 'world_pos':[], 'strings':[], 'objects':[]}
		mo_info['screen_pos'] = [(None, None)]
		mo_info['world_pos'] = [curr_world_pos.reshape(2,)]
		mo_info['strings'] = self.data['strings']
		mo_info['objects'] = [self]
		return mo_info

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['plot_moon'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['plot_moon_marker'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setMoonMarkerVisibility,
											'widget_data': None}
		self._dflt_opts['moon_marker_colour'] = {'value': (159,159,159),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMoonMarkerColour,
											'widget_data': None}
		self._dflt_opts['moon_marker_size'] = {'value': 30,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setMoonMarkerSize,
											'widget_data': None}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'][self.data['curr_index']].reshape(1,2),
											size=self.opts['moon_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['moon_marker_colour']['value']))

	def setMoonMarkerVisibility(self, state):
		self.opts['moon_sun_marker']['value'] = state
		self.visuals['marker'].visible = self.opts['plot_moon_marker']['value']

	def setMoonMarkerColour(self, new_colour):
		logger.debug("Changing moon marker colour %s -> %s", self.opts['moon_marker_colour']['value'], new_colour)
		self.opts['moon_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setMoonMarkerSize(self, size):
		logger.debug("Changing moon marker size %s -> %s", self.opts['moon_marker_size']['value'], size)
		self.opts['moon_marker_size']['value'] = size
		self._updateMarkers()
