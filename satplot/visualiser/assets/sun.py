import numpy as np
from scipy.spatial.transform import Rotation

from vispy import scene
from vispy.visuals import transforms as vTransforms
from vispy.scene import visuals as vVisuals
from vispy.visuals import filters as vFilters

import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.polyhedra as polyhedra
import satplot.util.constants as c
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.interface.console as console
import satplot.visualiser.colours as colours
import spherapy.orbit as orbit


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
			console.send(sun_pos)
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
											'widget': None}
		self._dflt_opts['plot_sun_sphere'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSunSphereVisibility,
											'widget': None}
		self._dflt_opts['sun_sphere_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunSphereColour,
											'widget': None}
		self._dflt_opts['plot_sun_vector'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setSunVectorVisibility,
											'widget': None}
		self._dflt_opts['sun_vector_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setSunVectorColour,
											'widget': None}
		self._dflt_opts['sun_vector_width'] = {'value': 1,
												'type': 'float',
												'help': '',
												'static': True,
												'callback': self.setSunVectorWidth,
											'widget': None}
		self._dflt_opts['sun_vector_length_kms'] = {'value': c.R_EARTH/3,
												'type': 'integer',
												'help': '',
												'static': True,
												'callback': self.setSunVectorLength,
											'widget': None}
		self._dflt_opts['plot_umbra'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setUmbraVisibility,
											'widget': None}
		self._dflt_opts['umbra_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setUmbraColour,
											'widget': None}
		self._dflt_opts['umbra_alpha'] = {'value': 0.25,
										  		'type': 'fraction',
												'help': '',
												'static': True,
												'callback': self.setUmbraAlpha,
											'widget': None}
		self._dflt_opts['umbra_dist'] = {'value': 3*c.R_EARTH,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setUmbraDistance,
											'widget': None}
		self._dflt_opts['sun_distance_kms'] = {'value': 15000,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSunDistance,
											'widget': None}
		self._dflt_opts['sun_sphere_radius_kms'] = {'value': 786,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setSunSphereRadius,
											'widget': None}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#	
	def _updateLineVisualsOptions(self):
		new_colour = colours.normaliseColour(self.opts['sun_vector_colour']['value'])
		print(f'Sun vector applied colour: {new_colour}')
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
		print(f"{self.opts['sun_vector_length_kms']['value']=}")
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
		print(f"Changing sun sphere colour {self.opts['sun_sphere_colour']['value']} -> {new_colour}")
		self.opts['sun_sphere_colour']['value'] = new_colour
		n_faces = self.visuals['sun_sphere'].mesh._meshdata.n_faces
		n_verts = self.visuals['sun_sphere'].mesh._meshdata.n_vertices
		self.visuals['sun_sphere'].mesh._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['sun_sphere'].mesh._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['sun_sphere'].mesh.mesh_data_changed()

	def setUmbraAlpha(self, alpha):
		# Takes a little while to take effect.
		print(f"Changing umbra alpha {self.opts['umbra_alpha']['value']} -> {alpha}")
		self.opts['umbra_alpha']['value'] = alpha
		self.data['umbra_alpha_filter'].alpha = alpha

	def setUmbraColour(self, new_colour):
		print(f"Changing umbra colour {self.opts['umbra_colour']['value']} -> {new_colour}")
		self.opts['umbra_colour']['value'] = new_colour
		n_faces = self.visuals['umbra']._meshdata.n_faces
		n_verts = self.visuals['umbra']._meshdata.n_vertices
		self.visuals['umbra']._meshdata.set_face_colors(np.tile(colours.normaliseColour(new_colour),(n_faces,1)))
		self.visuals['umbra']._meshdata.set_vertex_colors(np.tile(colours.normaliseColour(new_colour),(n_verts,1)))
		self.visuals['umbra'].mesh_data_changed()

	def setUmbraDistance(self, dist):
		print(f"Changing umbra dist {self.opts['umbra_dist']['value']} -> {dist}")
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
		print(f"Changing sun vector colour {self.opts['sun_vector_colour']['value']} -> {new_colour}")
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


