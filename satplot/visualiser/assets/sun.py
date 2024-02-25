import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons

from satplot.visualiser.controls import console

from vispy import scene
from vispy.visuals.transforms import STTransform

import numpy as np

class Sun(BaseAsset):
	def __init__(self, canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.ecef_rads = 0
		self.requires_recompute = False
		self._setDefaultOptions()	
		self.draw()

		# These callbacks need to be set after draw() as the option dict is populated during draw()
	
	def draw(self):
		self.addSunSphere()
		# self.addSunVector()
		# self.addSunUmbra()

	def compute():
		pass

	def setSource(self, source):
		self.data['pos'] = source.sun

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.data['curr_pos'] = self.data['pos'][self.data['curr_index']]
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.requires_recompute:			
			sun_pos = self.opts['sun_distance']['value'] * pg.unitVector(self.data['curr_pos'])
			self.visuals['sun'].transform = STTransform(translate=sun_pos)
			# rot_mat = transforms.rotAround(self.ecef_rads, pg.Z)
			# new_coords = rot_mat.dot(self.data['landmass'].T).T
			# self.visuals['landmass'].set_data(new_coords)

			for key, visual in self.visuals.items():
				if isinstance(visual,BaseAsset):
					pass

			self.requires_recompute = False

	def addSunSphere(self):
		self.visuals['sun'] = scene.visuals.Sphere(radius=self.opts['sun_sphere_radius']['value'],
										method='latitude',
										parent=self.parent,
										color=colours.normaliseColour(self.opts['sun_sphere_colour']['value']))		

	
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
		self._dflt_opts['sun_sphere_colour'] = {'value': (255,255,0),
												'type': 'colour',
												'help': '',
												'callback': self.setSunSphereColour}
		self._dflt_opts['plot_sun_vector'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setSunVectorVisibility}
		self._dflt_opts['sun_vector_colour'] = {'value': (255,255,0),
												'type': 'colour',
												'help': '',
												'callback': self.setSunVectorColour}
		self._dflt_opts['plot_umbra'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setUmbraVisibility}
		self._dflt_opts['umbra_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setUmbraColour}
		self._dflt_opts['umbra_alpha'] = {'value': 'number',
										  		'type': 1,
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
		raise NotImplementedError
		pass
		# self.opts['earth_axis_colour']['value'] = colours.normaliseColour(new_colour)
		# self.visuals['earth_axis'].set_data(color=colours.normaliseColour(new_colour))

	def setUmbraVisibility(self, state):
		raise NotImplementedError

	def setLandMassColour(self, new_colour):
		self.opts['landmass_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['landmass'].set_data(color=colours.normaliseColour(new_colour))

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