import logging
import numpy as np
import pymap3d
from typing import Any
from scipy.spatial import ConvexHull as ConvexHull
from scipy.spatial.transform import Rotation



import vispy
from vispy import scene
from vispy.visuals import transforms as vTransforms
from vispy.scene import visuals as vVisuals
from vispy.visuals import filters as vFilters

import satplot.model.data_models.history_data as history_data
import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.polygons as polygeom
import satplot.model.geometry.polyhedra as polyhedra
import satplot.model.geometry.spherical as spherical_geom
import satplot.util.array_u as array_u
import satplot.util.constants as c

import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours
import satplot.visualiser.visuals.polygons as polygon_visuals
import spherapy.orbit as orbit

logger = logging.getLogger(__name__)

class Sun3DAsset(base_assets.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Sun'
		self.data['umbra_start_axis'] = np.array((1,0,0)).reshape(1,3)
		self.data['umbra_vertices'], self.data['umbra_faces'] = \
						polyhedra.calcCylinderMesh((0,0,0),
												self.opts['umbra_dist']['value'],
												self.data['umbra_start_axis'],
												c.R_EARTH+50,
												axis_sample=2,
												theta_sample=30)
		self.data['vector_start_axis'] = np.array((1,0,0)).reshape(1,3)
		self.data['vector'] = np.asarray([[0,0,0,1],
										[c.R_EARTH/4,0,0,1]])
		self.data['vector_head_vertices'], self.data['vector_head_faces'] = \
						polyhedra.calcConeMesh((0,0,0),
												500,
												self.data['vector_start_axis'],
												45,
												axis_sample=2,
												theta_sample=30)
		self.data['umbra_alpha_filter'] = None

	def _reInitUmbraData(self):
		self.data['umbra_vertices'], self.data['umbra_faces'] = \
						polyhedra.calcCylinderMesh((0,0,0),
												self.opts['umbra_dist']['value'],
												self.data['umbra_start_axis'],
												c.R_EARTH+50,
												axis_sample=2,
												theta_sample=30)

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		self._createSunVisual()
		self._createUmbraVisual()
		self._createVectorVisual()

	def _createSunVisual(self):
		# Sun Sphere
		self.visuals['sun_sphere'] = scene.visuals.Sphere(radius=self.opts['sun_sphere_radius_kms']['value'],
										method='latitude',
										color=colours.normaliseColour(self.opts['sun_sphere_colour']['value']),
										parent=None)

	def _createUmbraVisual(self):
		# Umbra
		self.visuals['umbra'] = vVisuals.Mesh(self.data['umbra_vertices'],
												self.data['umbra_faces'],
												color=colours.normaliseColour(self.opts['umbra_colour']['value']),
												parent=None)
		# Apply shrinking transform to hide umbra till it needs to be first drawn
		self.visuals['umbra'].transform = vTransforms.STTransform(scale=(0.001,0.001,0.001))
		self.data['umbra_alpha_filter'] = vFilters.Alpha(self.opts['umbra_alpha']['value'])
		self.visuals['umbra'].attach(self.data['umbra_alpha_filter'])

		#TODO: Better shadow display, but shows through earth, maybe cut out spherical cap
		# self.visuals['umbra'].set_gl_state(depth_test=False)
		# self.visuals['umbra'].set_gl_state('translucent')
		# self.visuals['umbra'].set_gl_state('translucent', cull_face=True)
		# self.visuals['umbra'].set_gl_state('translucent', depth_test=False) <---
		# self.visuals['umbra'].set_gl_state('translucent', blend=False)
		# self.visuals['umbra'].set_gl_state('translucent', blend=False, depth_test=False)
		# self.visuals['umbra'].set_gl_state('translucent', cull_face=True, depth_test=False)
		# self.visuals['umbra'].set_gl_state('translucent', cull_face=True, blend=False)

	def _createVectorVisual(self):
		# Sun Vector
		self.visuals['vector_body'] = vVisuals.Line(self.data['vector'][:,0:3],
												color=colours.normaliseColour(self.opts['sun_vector_colour']['value']),
												width=self.opts['sun_vector_width']['value'],
												parent=None)

		self.visuals['vector_head'] = vVisuals.Mesh(self.data['vector_head_vertices'],
												self.data['vector_head_faces'],
												color=colours.normaliseColour(self.opts['sun_vector_colour']['value']),
												parent=None)

	def setSource(self, *args, **kwargs):
		sats_dict = args[0]
		first_sat_orbit = list(sats_dict.values())[0]
		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error("data source for %s is not an orbit.Orbit, can't extract sun location data", self)
			raise TypeError

		self.data['pos'] = first_sat_orbit.sun_pos

	# Override AbstractAsset.updateIndex()
	def updateIndex(self, index):
		self.setStaleFlagRecursive()
		self.data['curr_index'] = index
		self.data['curr_pos'] = self.data['pos'][self.data['curr_index']]
		self._updateIndexChildren(index)

	def recomputeRedraw(self):
		if self.isFirstDraw():
			# In vispy, mesh transparency will not show visuals through it which have been added to the scene (by makeActive in satplot)
			# Therefore any asset with a transparent mesh should detach then reattach to ensure solid objects inside the mesh are seen
			# from outside.
			# The order of calling recomputeRedraw() will determine what is displayed with nested meshes.
			self._detachFromParentView()
			self._attachToParentView()

			self._clearFirstDrawFlag()
		if self.isStale():
			# move the sun
			sun_pos = self.opts['sun_distance_kms']['value'] * pg.unitVector(self.data['curr_pos'])
			self.visuals['sun_sphere'].transform = vTransforms.STTransform(translate=sun_pos)
			# move umbra
			umbra_dir = (-1*self.data['curr_pos']).reshape(1,3)
			rot_mat = Rotation.align_vectors(self.data['umbra_start_axis'], umbra_dir)[0].as_matrix()
			t_mat1 = np.eye(4)
			t_mat1[0:3,0:3] = rot_mat
			self.visuals['umbra'].transform = vTransforms.linear.MatrixTransform(t_mat1)

			# move sun vector
			sun_vec_start = (np.linalg.norm(sun_pos)-self.opts['sun_vector_length_kms']['value'])*pg.unitVector(sun_pos)
			arrow_head_point = (np.linalg.norm(sun_pos)-self.opts['sun_vector_length_kms']['value']-500)*pg.unitVector(sun_pos)
			sun_vec_end = sun_pos
			t_mat2 = np.eye(4)
			t_mat2[0:3,0:3] = -rot_mat
			t_mat2[3,0:3] = arrow_head_point
			new_vec = np.vstack((sun_vec_start,
								sun_vec_end))
			self.visuals['vector_body'].set_data(new_vec)
			self.visuals['vector_head'].transform = vTransforms.linear.MatrixTransform(t_mat2)


			self._recomputeRedrawChildren()
			self._clearStaleFlag()

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['plot_sun'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['plot_sun_sphere'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSunSphereVisibility,
											'widget_data': None}
		self._dflt_opts['sun_sphere_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunSphereColour,
											'widget_data': None}
		self._dflt_opts['plot_sun_vector'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSunVectorVisibility,
											'widget_data': None}
		self._dflt_opts['sun_vector_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunVectorColour,
											'widget_data': None}
		self._dflt_opts['sun_vector_width'] = {'value': 1,
												'type': 'float',
												'help': '',
												'static': True,
												'callback': self.setSunVectorWidth,
											'widget_data': None}
		self._dflt_opts['sun_vector_length_kms'] = {'value': c.R_EARTH/3,
												'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setSunVectorLength,
											'widget_data': None}
		self._dflt_opts['plot_umbra'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setUmbraVisibility,
											'widget_data': None}
		self._dflt_opts['umbra_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setUmbraColour,
											'widget_data': None}
		self._dflt_opts['umbra_alpha'] = {'value': 0.25,
												'type': 'fraction',
												'help': '',
												'static': True,
												'callback': self.setUmbraAlpha,
											'widget_data': None}
		self._dflt_opts['umbra_dist'] = {'value': 3*c.R_EARTH,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setUmbraDistance,
											'widget_data': None}
		self._dflt_opts['sun_distance_kms'] = {'value': 15000,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSunDistance,
											'widget_data': None}
		self._dflt_opts['sun_sphere_radius_kms'] = {'value': 786,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSunSphereRadius,
											'widget_data': None}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateLineVisualsOptions(self):
		new_colour = colours.normaliseColour(self.opts['sun_vector_colour']['value'])
		logger.debug('Sun vector applied colour: %s', new_colour)
		self.visuals['vector_body'].set_data(color=new_colour,
												width=self.opts['sun_vector_width']['value'])

	def setSunSphereVisibility(self, state):
		self.opts['plot_sun_sphere']['value'] = state
		self.visuals['sun_sphere'].visible = self.opts['plot_sun_sphere']['value']

	def setSunDistance(self, distance):
		self.opts['sun_distance_kms']['value'] = distance
		# TODO: fix this to set stale then recomputeredraw, maybe firstdraw as well
		self.setStaleFlagRecursive()
		self.recomputeRedraw()

	def setSunVectorLength(self, distance):
		self.opts['sun_vector_length_kms']['value'] = distance
		self._setStaleFlag()
		self.recomputeRedraw()

	def setSunSphereRadius(self, radius):
		self.opts['sun_sphere_radius_kms']['value'] = radius
		self._detachFromParentView()
		self._createSunVisual()
		self._attachToParentView()
		self._setStaleFlag()
		self.recomputeRedraw()

	def setSunSphereColour(self, new_colour):
		logger.debug("Changing sun sphere colour %s -> %s", self.opts['sun_sphere_colour']['value'], new_colour)
		self.opts['sun_sphere_colour']['value'] = new_colour
		n_faces = self.visuals['sun_sphere'].mesh._meshdata.n_faces
		n_verts = self.visuals['sun_sphere'].mesh._meshdata.n_vertices
		self.visuals['sun_sphere'].mesh._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['sun_sphere'].mesh._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['sun_sphere'].mesh.mesh_data_changed()

	def setUmbraAlpha(self, alpha):
		# Takes a little while to take effect.
		logger.debug("Changing umbra alpha %s -> %s", self.opts['umbra_alpha']['value'], alpha)
		self.opts['umbra_alpha']['value'] = alpha
		self.data['umbra_alpha_filter'].alpha = alpha

	def setUmbraColour(self, new_colour):
		logger.debug("Changing umbra colour %s -> %s", self.opts['umbra_colour']['value'], new_colour)
		self.opts['umbra_colour']['value'] = new_colour
		n_faces = self.visuals['umbra']._meshdata.n_faces
		n_verts = self.visuals['umbra']._meshdata.n_vertices
		self.visuals['umbra']._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['umbra']._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['umbra'].mesh_data_changed()

	def setUmbraDistance(self, dist):
		logger.debug("Changing umbra dist %s -> %s", self.opts['umbra_dist']['value'], dist)
		self.opts['umbra_dist']['value'] = dist
		self._reInitUmbraData()
		self.visuals['umbra']._meshdata.set_faces(self.data['umbra_faces'])
		self.visuals['umbra']._meshdata.set_vertices(self.data['umbra_vertices'])
		self.visuals['umbra'].mesh_data_changed()

	def setUmbraVisibility(self, state):
		self.opts['plot_umbra']['value'] = state
		self.visuals['umbra'].visible = self.opts['plot_umbra']['value']

	def setSunVectorVisibility(self, state):
		self.opts['plot_sun_vector']['value'] = state
		self.visuals['vector_body'].visible = self.opts['plot_sun_vector']['value']
		self.visuals['vector_head'].visible = self.opts['plot_sun_vector']['value']


	def setSunVectorColour(self, new_colour):
		logger.debug("Changing sun vector colour %s -> %s", self.opts['sun_vector_colour']['value'], new_colour)
		self.opts['sun_vector_colour']['value'] = new_colour
		self._updateLineVisualsOptions()
		n_faces = self.visuals['vector_head']._meshdata.n_faces
		n_verts = self.visuals['vector_head']._meshdata.n_vertices
		self.visuals['vector_head']._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['vector_head']._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['vector_head'].mesh_data_changed()

	def setSunVectorWidth(self, value):
		self.opts['sun_vector_width']['value'] = value
		self._updateLineVisualsOptions()




class Sun2DAsset(base_assets.AbstractAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Sun'
		self.data['coords'] = np.zeros((4,2))
		self.data['scaled_coords'] = np.zeros((4,2))
		self.data['curr_index'] = 0

		self.data['terminator_edge'] = -1*np.ones((364,2))
		# need to create a valid polygon for instantiation (but before valid data exists)
		self.data['terminator_edge'][:363,0] = np.arange(0,363)
		self.data['terminator_edge'][-1,1] = -1
		self.data['terminator_edge'][-2,1] = -2

		self.data['eclipse_edge'] = -1*np.ones((180,2))
		# need to create a valid polygon for instantiation (but before valid data exists)
		self.data['eclipse_edge'][:179,0] = np.arange(0,179)
		self.data['eclipse_edge'][-1,1] = -1
		self.data['eclipse_edge'][-2,1] = -2

		self.data['eclipse_edge1'] = self.data['eclipse_edge'].copy()
		self.data['eclipse_edge2'] = self.data['eclipse_edge'].copy()
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
										face_color=colours.normaliseColour(self.opts['sun_marker_colour']['value']),
										edge_color='white',
										size=self.opts['sun_marker_size']['value'],
										symbol='o')
		self.visuals['marker'].order = -1


		self.visuals['terminator'] = polygon_visuals.FastPolygon(self.data['terminator_edge'], color='#000000', border_color='#000000', border_width=0, parent=None)
		self.visuals['terminator'].opacity = self.opts['terminator_alpha']['value']
		self.visuals['terminator'].order = 1
		self.visuals['terminator'].set_gl_state('translucent', depth_test=False)

		self.visuals['eclipse_patch1'] = polygon_visuals.FastPolygon(self.data['eclipse_edge'], color='#000000', border_color='#000000', border_width=0, parent=None)

		self.visuals['eclipse_patch1'].opacity = self.opts['eclipse_alpha']['value']
		self.visuals['eclipse_patch1'].order = 2
		self.visuals['eclipse_patch1'].set_gl_state('translucent', depth_test=False)
		self.visuals['eclipse_patch2'] = polygon_visuals.FastPolygon(self.data['eclipse_edge'], color='#000000', border_color='#000000', border_width=0, parent=None)
		self.visuals['eclipse_patch2'].opacity = self.opts['eclipse_alpha']['value']
		self.visuals['eclipse_patch2'].order = 2
		self.visuals['eclipse_patch2'].set_gl_state('translucent', depth_test=False)

	def setSource(self, *args, **kwargs):
		# args[0] history data
		if type(args[0]) is not history_data.HistoryData:
			logger.error("setSource() of %s requires a %s as args[1], not: %s", self, history_data.HistoryData, type(args[1]))
			raise TypeError(f"setSource() of {self} requires a {history_data.HistoryData} as args[1], not: {type(args[1])}")
			return

		self.data['history_src'] = args[0]
		first_sat_orbit = list(self.data['history_src'].getOrbits().values())[0]

		if type(first_sat_orbit) is not orbit.Orbit:
			logger.error("data source for %s is not an orbit.Orbit, can't extract sun location data", self)
			raise TypeError

		lat, lon, alt = pymap3d.eci2geodetic(first_sat_orbit.sun_pos[:,0],
											first_sat_orbit.sun_pos[:,1],
											first_sat_orbit.sun_pos[:,2],
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
			# move the sun
			self._updateMarkers()
			terminator_boundary = self.calcTerminatorOutline(self.data['coords'][self.data['curr_index']])

			self.data['terminator_edge'][:,0] = (terminator_boundary[:,0]+180) * self.data['horiz_pixel_scale']
			self.data['terminator_edge'][:,1] = (terminator_boundary[:,1]+90) * self.data['vert_pixel_scale']

			self.visuals['terminator'].pos = self.data['terminator_edge']

			self.data['eclipse_edge1'], self.data['eclipse_edge2'], split = self.calcEclipseOutline(self.data['coords'][self.data['curr_index']], np.linalg.norm(self.data['coords'][self.data['curr_index']]))

			self.visuals['eclipse_patch1'].pos = self.data['eclipse_edge1']
			self.visuals['eclipse_patch2'].pos = self.data['eclipse_edge2']

			if split:
				self.visuals['eclipse_patch1'].opacity = self.opts['eclipse_alpha']['value']
				self.visuals['eclipse_patch2'].opacity = self.opts['eclipse_alpha']['value']
			else:
				self.visuals['eclipse_patch1'].opacity = self.opts['eclipse_alpha']['value']/2
				self.visuals['eclipse_patch2'].opacity = self.opts['eclipse_alpha']['value']/2

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
		self._dflt_opts['plot_sun'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setVisibility,
											'widget_data': None}
		self._dflt_opts['plot_sun_marker'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSunMarkerVisibility,
											'widget_data': None}
		self._dflt_opts['sun_marker_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunMarkerColour,
											'widget_data': None}
		self._dflt_opts['plot_terminator'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setTerminatorVisibility,
											'widget_data': None}
		self._dflt_opts['plot_eclipse'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setEclipseVisibility,
											'widget_data': None}
		self._dflt_opts['terminator_colour'] = {'value': (0,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setTerminatorColour,
											'widget_data': None}
		self._dflt_opts['eclipse_colour'] = {'value': (0,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setEclipseColour,
											'widget_data': None}
		self._dflt_opts['terminator_alpha'] = {'value': 0.4,
												'type': 'fraction',
												'help': '',
												'static': True,
												'callback': self.setTerminatorAlpha,
												'widget_data': None}
		self._dflt_opts['eclipse_alpha'] = {'value': 0.4,
												'type': 'fraction',
												'help': '',
												'static': True,
												'callback': self.setEclipseAlpha,
												'widget_data': None}
		self._dflt_opts['sun_marker_size'] = {'value': 30,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSunMarkerSize,
											'widget_data': None}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def _updateMarkers(self):
		self.visuals['marker'].set_data(pos=self.data['scaled_coords'][self.data['curr_index']].reshape(1,2),
											size=self.opts['sun_marker_size']['value'],
											face_color=colours.normaliseColour(self.opts['sun_marker_colour']['value']))

	def setSunMarkerVisibility(self, state):
		self.opts['plot_sun_marker']['value'] = state
		self.visuals['marker'].visible = self.opts['plot_sun_marker']['value']

	def setSunMarkerColour(self, new_colour):
		logger.debug("Changing sun marker colour %s -> %s", self.opts['sun_marker_colour']['value'], new_colour)
		self.opts['sun_marker_colour']['value'] = new_colour
		self._updateMarkers()

	def setSunMarkerSize(self, size):
		logger.debug("Changing sun marker size %s -> %s", self.opts['sun_marker_size']['value'], size)
		self.opts['sun_marker_size']['value'] = size
		self._updateMarkers()

	def setTerminatorAlpha(self, alpha):
		# Takes a little while to take effect.
		logger.debug("Changing terminator alpha %s -> %s", self.opts['terminator_alpha']['value'], alpha)
		self.opts['terminator_alpha']['value'] = alpha
		self.visuals['terminator'].opacity = self.opts['terminator_alpha']['value']

	def setEclipseAlpha(self, alpha):
		# Takes a little while to take effect.
		logger.debug("Changing eclipse alpha %s -> %s", self.opts['eclipse_alpha']['value'], alpha)
		self.opts['eclipse_alpha']['value'] = alpha
		self.visuals['eclipse_patch1'].opacity = self.opts['eclipse_alpha']['value']
		self.visuals['eclipse_patch2'].opacity = self.opts['eclipse_alpha']['value']

	def setTerminatorColour(self, new_colour):
		logger.debug("Changing terminator colour %s -> %s", self.opts['terminator_colour']['value'], new_colour)
		self.opts['terminator_colour']['value'] = new_colour
		self.visuals['terminator'].color = self.opts['terminator_colour']['value']

	def setEclipseColour(self, new_colour):
		logger.debug("Changing eclipse colour %s -> %s", self.opts['eclipse_colour']['value'], new_colour)
		self.opts['eclipse_colour']['value'] = new_colour
		self.visuals['eclipse_patch1'].color = self.opts['eclipse_colour']['value']
		self.visuals['eclipse_patch2'].color = self.opts['eclipse_colour']['value']

	def setTerminatorVisibility(self, state):
		self.opts['plot_terminator']['value'] = state
		self.visuals['terminator'].visible = self.opts['plot_terminator']['value']

	def setEclipseVisibility(self, state):
		self.opts['plot_eclipse']['value'] = state
		self.visuals['eclipse_patch1'].visible = self.opts['plot_eclipse']['value']
		self.visuals['eclipse_patch2'].visible = self.opts['plot_eclipse']['value']

	def getTerminatorPoint(self, earth_lon:float|np.ndarray, solar_lat:float, solar_lon:float) -> float:
		ha = earth_lon - solar_lon
		return np.arctan(-np.cos(ha)/np.tan(solar_lat))

	def calcTerminatorOutline(self, solar_lonlat) -> np.ndarray:
		terminator_boundary = np.zeros((361,2))
		solar_lat = solar_lonlat[1]
		solar_lon = solar_lonlat[0]
		terminator_boundary[:,0] = np.arange(-180,181,1)
		terminator_boundary[:,1] = np.rad2deg(self.getTerminatorPoint(np.deg2rad(terminator_boundary[:,0]), np.deg2rad(solar_lat), np.deg2rad(solar_lon)))

		if solar_lat > 0:
			terminator_boundary = np.vstack((np.array((-180,-90)),terminator_boundary))
			terminator_boundary = np.vstack((terminator_boundary, np.array((180,-90))))
			terminator_boundary = np.vstack((terminator_boundary, np.array((-180,-90))))

		elif solar_lat < 0:
			terminator_boundary = np.vstack((np.array((-180,90)),terminator_boundary))
			terminator_boundary = np.vstack((terminator_boundary, np.array((180,90))))
			terminator_boundary = np.vstack((terminator_boundary, np.array((-180,90))))

		else:
			pass

		return terminator_boundary

	def calcEclipseOutline(self, solar_lonlat, sat_altitude) -> tuple[np.ndarray, np.ndarray, bool]:
		# sat altitude in km
		# half subtended angle = phi_h
		eclipse_center_lat = -solar_lonlat[1]
		eclipse_center_lon = np.rad2deg(spherical_geom.wrapToCircleRange(np.deg2rad(solar_lonlat[0] + 180)))
		solar_lat = solar_lonlat[1]
		phi_h = np.rad2deg(np.arcsin(c.R_EARTH/(c.R_EARTH+sat_altitude)))
		lats, lons1, lons2 = spherical_geom.genSmallCircleCenterSubtendedAngle(phi_h*2, eclipse_center_lat, eclipse_center_lon)
		circle1, circle2 = spherical_geom.splitSmallCirclePatch(eclipse_center_lon, eclipse_center_lat, lats, lons1, lons2)

		if np.all(circle1 == circle2):
			split = False
		else:
			split = True

		return self._scale(circle1), self._scale(circle2), split

	def _scale(self, coords):
		out_arr = coords.copy()
		out_arr[:,0] = (out_arr[:,0] + 180) * self.data['horiz_pixel_scale']
		out_arr[:,1] = (out_arr[:,1] + 90) * self.data['vert_pixel_scale']
		return out_arr