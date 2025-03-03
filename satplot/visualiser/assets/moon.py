import numpy as np

import vispy.scene as scene
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.transforms as vtransforms

import satplot.model.geometry.primgeom as pg
import satplot.util.constants as c
import satplot.visualiser.colours as colours
import satplot.visualiser.assets.base_assets as base_assets
import spherapy.orbit as orbit


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
			raise TypeError
		self.data['pos'] = args[0].moon_pos

	def _instantiateAssets(self) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['moon'] = scene.visuals.Sphere(radius=self.opts['moon_sphere_radius_kms']['value'],
												method='latitude',
												color=colours.normaliseColour(self.opts['moon_sphere_colour']['value']),
												parent=None)
		self._constructVisibilityStruct()

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
												'callback': self.setVisibility,
											'widget': None}
		self._dflt_opts['moon_sphere_colour'] = {'value': (61,61,61),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setMoonSphereColour,
											'widget': None}
		self._dflt_opts['moon_distance_kms'] = {'value': 15000,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setMoonDistance,
											'widget': None}
		self._dflt_opts['moon_sphere_radius_kms'] = {'value': 786,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setMoonSphereRadius,
											'widget': None}

		# moon radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()
	
	#----- OPTIONS CALLBACKS -----#
	def setMoonSphereColour(self, new_colour:tuple[float,float,float]) -> None:
		print(f"Changing moon sphere colour {self.opts['moon_sphere_colour']['value']} -> {new_colour}")
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

