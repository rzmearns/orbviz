import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons
from satplot.model.geometry import polyhedra

from satplot.visualiser.controls import console

from vispy import scene
from vispy.visuals import transforms as vTransforms
from vispy.scene import visuals as vVisuals
from vispy.scene import visuals as vVisuals
from vispy.visuals import filters as vFilters

from scipy.spatial.transform import Rotation

import numpy as np

class Sun(BaseAsset):
	def __init__(self, canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.ecef_rads = 0
		self.requires_recompute = False
		self.first_draw = True
		self._setDefaultOptions()	
		self.draw()
		self.visuals['umbra'] = None

		# These callbacks need to be set after draw() as the option dict is populated during draw()
	
	def draw(self):
		self.addSunSphere()
		self.addSunVector()

	def compute():
		pass

	def setSource(self, source):
		self.data['pos'] = source.sun

	def setFirstDraw(self):
		self.first_draw = True

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.data['curr_pos'] = self.data['pos'][self.data['curr_index']]
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.first_draw:
			if self.visuals['umbra'] is not None:
				# Must do this to clear old visuals before creating a new one
				# TODO: not clear if this is actually deleting or just removing the reference (memory leak?)
				self.visuals['umbra'].parent = None
			console.send("Adding umbra")
			self.addUmbra()
			self.first_draw = False
		if self.requires_recompute:
			# move the sun
			sun_pos = self.opts['sun_distance']['value'] * pg.unitVector(self.data['curr_pos'])
			self.visuals['sun'].transform = vTransforms.STTransform(translate=sun_pos)
			# move umbra
			umbra_dir = (-1*self.data['curr_pos']).reshape(1,3)
			rot_mat = Rotation.align_vectors(self.data['umbra_start_axis'], umbra_dir)[0].as_matrix()
			t_mat1 = np.eye(4)
			t_mat1[0:3,0:3] = rot_mat
			self.visuals['umbra'].transform = vTransforms.linear.MatrixTransform(t_mat1)
			# move sun vector
			sun_vec_start = (np.linalg.norm(sun_pos)-self.opts['sun_vector_length']['value'])*pg.unitVector(sun_pos)
			arrow_head_point = (np.linalg.norm(sun_pos)-self.opts['sun_vector_length']['value']-500)*pg.unitVector(sun_pos)
			sun_vec_end = sun_pos
			t_mat2 = np.eye(4)
			t_mat2[0:3,0:3] = -rot_mat
			t_mat2[3,0:3] = arrow_head_point
			new_vec = np.vstack((sun_vec_start,
								sun_vec_end))
			self.visuals['vector_body'].set_data(new_vec)
			self.visuals['vector_head'].transform = vTransforms.linear.MatrixTransform(t_mat2)

			for key, visual in self.visuals.items():
				if isinstance(visual,BaseAsset):
					pass

			self.requires_recompute = False

	def addSunSphere(self):
		self.visuals['sun'] = scene.visuals.Sphere(radius=self.opts['sun_sphere_radius']['value'],
										method='latitude',
										parent=self.parent,
										color=colours.normaliseColour(self.opts['sun_sphere_colour']['value']))

	def addUmbra(self):
		self.data['umbra_start_axis'] = np.array((1,0,0)).reshape(1,3)
		self.data['umbra_vertices'], self.data['umbra_faces'] = polyhedra.calcCylinderMesh((0,0,0),
																					 	self.opts['umbra_dist']['value'],
																						self.data['umbra_start_axis'],
																						c.R_EARTH+50,
																						axis_sample=2,
																						theta_sample=30)
		self.visuals['umbra'] = vVisuals.Mesh(self.data['umbra_vertices'],
    											self.data['umbra_faces'],
    											color=colours.normaliseColour(self.opts['umbra_colour']['value']),
    											parent=self.parent)
		self.visuals['umbra'].transform = vTransforms.STTransform(scale=(0.001,0.001,0.001))
		alpha_filter = vFilters.Alpha(self.opts['umbra_alpha']['value'])
		self.visuals['umbra'].attach(alpha_filter)

	def addSunVector(self):
		self.data['vector_start_axis'] = np.array((1,0,0)).reshape(1,3)
		self.data['vector'] = np.asarray([[0,0,0,1],
										[c.R_EARTH/4,0,0,1]])
		self.visuals['vector_body'] = vVisuals.Line(self.data['vector'][:,0:3],
												color=colours.normaliseColour(self.opts['sun_vector_colour']['value']),
												width=self.opts['sun_vector_width']['value'],
												parent=self.parent)
		self.data['vector_head_vertices'], self.data['vector_head_faces'] = polyhedra.calcConeMesh((0,0,0),
																					 	500,
																						(1,0,0),
																						45,
																						axis_sample=2,
																						theta_sample=30)		
		self.visuals['vector_head'] = vVisuals.Mesh(self.data['vector_head_vertices'],
    											self.data['vector_head_faces'],
    											color=colours.normaliseColour(self.opts['sun_vector_colour']['value']),
    											parent=self.parent)

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': self.setAntialias}
		self._dflt_opts['plot_sun'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setSunAssetVisibility}
		self._dflt_opts['plot_sun_sphere'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setSunSphereVisibility}
		self._dflt_opts['sun_sphere_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'callback': self.setSunSphereColour}
		self._dflt_opts['plot_sun_vector'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setSunVectorVisibility}
		self._dflt_opts['sun_vector_colour'] = {'value': (255,162,0),
												'type': 'colour',
												'help': '',
												'callback': self.setSunVectorColour}
		self._dflt_opts['sun_vector_width'] = {'value': 1,
												'type': 'number',
												'help': '',
												'callback': None}
		self._dflt_opts['sun_vector_length'] = {'value': c.R_EARTH/3,
												'type': 'number',
												'help': '',
												'callback': None}		
		self._dflt_opts['plot_umbra'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setUmbraVisibility}
		self._dflt_opts['umbra_colour'] = {'value': (10,10,10),
												'type': 'colour',
												'help': '',
												'callback': self.setUmbraColour}
		self._dflt_opts['umbra_alpha'] = {'value': 0.5,
										  		'type': 'number',
												'help': '',
												'callback': self.setUmbraAlpha}
		self._dflt_opts['umbra_dist'] = {'value': 3*c.R_EARTH,
										  		'type': 'number',
												'help': '',
												'callback': self.setUmbraAlpha}		
		self._dflt_opts['sun_distance'] = {'value': 15000,
										  		'type': 'number',
												'help': '',
												'callback': self.setSunDistance}
		self._dflt_opts['sun_sphere_radius'] = {'value': 786,
										  		'type': 'number',
												'help': '',
												'callback': self.setSunSphereRadius}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass
	
	def setSunAssetVisibility(self, state):
		self.setSunSphereVisibility(state)
		self.setUmbraVisibility(state)

	def setSunSphereColour(self, new_colour):
		raise NotImplementedError('Bugged')
		# nnc = colours.normaliseColour(new_colour)
		# annc = (nnc[0], nnc[1], nnc[2], 1)
		# self.opts['earth_sphere_colour']['value'] = new_colour
		# c = color.Color(color=nnc, alpha=1)
		# print(c)
		# print(self.opts['earth_sphere_colour']['value'])
		# self.visuals['earth'].mesh.set_data(vertex_colors=colours.normaliseColour(new_colour))
		# # self.visuals['earth'].mesh.mesh_data._face_colors_indexed_by_faces[:] = colours.normaliseColour(new_colour)
		# # self.visuals['earth'].mesh.mesh_data_changed()
		# # self.visuals['earth'].mesh.mesh_data.set_vertex_colors(nnc)
		# # self.visuals['earth'].mesh.mesh_data_changed()
		# self.visuals['earth'].mesh.set_data(color=c)
		# self.visuals['earth'].mesh.update()

	def setUmbraColour(self, new_colour):		
		self.opts['umbra_colour']['value'] = new_colour
		self.visuals['umbra'].set_data(color=colours.normaliseColour(new_colour))

	def setUmbraVisibility(self, state):
		self.visuals['umbra'].visible = state

	def setSunSphereVisibility(self, state):
		self.visuals['sun'].visible = state

	def setAntialias(self, state):
		raise NotImplementedError

	def setSunVectorVisibility(self, state):
		raise NotImplementedError

	def setSunVectorColour(self, new_colour):
		raise NotImplementedError

	def setUmbraAlpha(self, alpha):
		raise NotImplementedError

	def setSunDistance(self, distance):
		raise NotImplementedError

	def setSunSphereRadius(self, radius):
		raise NotImplementedError