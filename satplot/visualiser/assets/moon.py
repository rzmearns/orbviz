import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.controls import console

from satplot.model.geometry import primgeom as pg
import satplot.model.orbit as orbit

from vispy import scene
from vispy.visuals.transforms import STTransform

import numpy as np

class Moon(BaseAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		
		self.attachToParentView()
	
	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Moon'		
		self.data['curr_pos'] = None
		self.data['pos'] = None

	def setSource(self, *args, **kwargs):
		if type(args[0]) is not orbit.Orbit:
			raise TypeError
		self.data['pos'] = args[0].moon

	def _instantiateAssets(self):
		pass

	def _createVisuals(self):
		self.visuals['moon'] = scene.visuals.Sphere(radius=self.opts['moon_sphere_radius']['value'],
												method='latitude',
												color=colours.normaliseColour(self.opts['moon_sphere_colour']['value']),
												parent=None)

	def updateIndex(self, new_index):
		self.data['curr_index'] = new_index
		self.data['curr_pos'] = self.data['pos'][self.data['curr_index']]
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.first_draw:
			self.first_draw = False
		if self.requires_recompute:			
			moon_pos = self.opts['moon_distance']['value'] * pg.unitVector(self.data['curr_pos'])
			self.visuals['moon'].transform = STTransform(translate=moon_pos)

			for asset in self.assets.values():
				asset.recompute()

			self.requires_recompute = False
	
	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': self.setAntialias}
		self._dflt_opts['plot_moon'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setVisibility}
		self._dflt_opts['moon_sphere_colour'] = {'value': (61,61,61),
												'type': 'colour',
												'help': '',
												'callback': self.setMoonSphereColour}
		self._dflt_opts['moon_distance'] = {'value': 15000,
										  		'type': 'number',
												'help': '',
												'callback': self.setMoonDistance}
		self._dflt_opts['moon_sphere_radius'] = {'value': 786,
										  		'type': 'number',
												'help': '',
												'callback': self.setMoonSphereRadius}
		self._dflt_opts['moon_sphere_angular_size'] = {'value': 6,
										  		'type': 'number',
												'help': '',
												'callback': self.setMoonSphereAngularSize}		

		# moon radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()
	
	#----- OPTIONS CALLBACKS -----#
	def setMoonSphereColour(self, new_colour):
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

	def setAntialias(self, state):
		raise NotImplementedError

	def setMoonDistance(self, distance):
		raise NotImplementedError

	def setMoonSphereRadius(self, radius):
		raise NotImplementedError
	
	def setMoonSphereAngularSize(self, radius):
		raise NotImplementedError
