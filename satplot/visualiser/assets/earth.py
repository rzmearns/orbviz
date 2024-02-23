import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons



import geopandas as gpd

from vispy import scene, color

import numpy as np

class Earth(BaseAsset):
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
		self.opts['plot_meridians']['callback'] = self.visuals['meridians'].setMeridianVisibility
		self.opts['plot_parallels']['callback'] = self.visuals['parallels'].setParallelsVisibility
		self.opts['plot_equator']['callback'] = self.visuals['parallels'].setEquatorVisibility

		self.axis_gizmo = axisInd.XYZAxis(scale=(c.R_EARTH+1500), parent=parent)
	
	def draw(self):
		self.addEarthSphere()
		self.addEarthAxis()
		self.addLandMass()
		self.visuals['parallels'] = ParallelsGrid(self.parent)
		self.visuals['meridians'] = MeridiansGrid(self.parent)

	def compute():
		pass

	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def setCurrentECEFRotation(self, radians):
		self.ecef_rads = radians
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.requires_recompute:
			rot_mat = transforms.rotAround(self.ecef_rads, pg.Z)
			new_coords = rot_mat.dot(self.data['landmass'].T).T
			self.visuals['landmass'].set_data(new_coords)

			for key, visual in self.visuals.items():
				if isinstance(visual,BaseAsset):
					visual.setCurrentECEFRotation(self.ecef_rads)

			self.requires_recompute = False

	def addEarthSphere(self):
		self.visuals['earth'] = scene.visuals.Sphere(radius=c.R_EARTH,
										method='latitude',
										parent=self.parent,
										color=colours.normaliseColour(self.opts['earth_sphere_colour']['value']))

	def addEarthAxis(self):
		self.coords = np.zeros((2,3))
		self.coords[0,2] = -1*(c.R_EARTH+1000)
		self.coords[1,2] = (c.R_EARTH+1000)
		self.visuals['earth_axis'] = scene.visuals.Line(self.coords,
								 		color=colours.normaliseColour(self.opts['earth_axis_colour']['value']),
										parent=self.parent)

	def addLandMass(self):
		gdf = gpd.read_file('data/land_boundaries/ne_110m_land.shp')
		conn = None
		total_len = 0
		all_coords = None
		for ii in gdf.index:
			polys = gdf.loc[ii].geometry
			if polys.geom_type == 'Polygon':
				coords = self._convertShapeFilePolys(polys)		
				poly_len = len(coords)				
				new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
				if conn is not None:
					conn = np.vstack((conn,new_conn))
				else:
					conn = new_conn
				total_len += poly_len
				if all_coords is not None:
					all_coords = np.vstack((all_coords, coords))
				else:
					all_coords = coords

		self.data['landmass'] = all_coords

		self.visuals['landmass'] = scene.visuals.Line(all_coords,
													color=colours.normaliseColour(self.opts['landmass_colour']['value']),
													antialias=self.opts['antialias']['value'],
													connect=conn,
													parent=self.parent)
	
	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_earth_sphere'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setEarthSphereVisibility}
		self._dflt_opts['earth_sphere_colour'] = {'value': (220,220,220),
												'type': 'colour',
												'help': '',
												'callback': self.setEarthSphereColour}
		self._dflt_opts['plot_earth_axis'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setEarthAxisVisibility}
		self._dflt_opts['earth_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setEarthAxisColour}
		self._dflt_opts['plot_parallels'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': None}
		self._dflt_opts['plot_equator'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': None}
		self._dflt_opts['plot_meridians'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': None}
		self._dflt_opts['plot_landmass'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setLandmassVisibility}
		self._dflt_opts['landmass_colour'] = {'value': (0,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setLandMassColour}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass
	
	def _convertShapeFilePolys(self, poly):
		xy_coords = poly.exterior.coords.xy
		lon = np.array(xy_coords[0])
		lat = np.array(xy_coords[1])
		lon = lon * np.pi/180
		lat = lat * np.pi/180
		R = c.R_EARTH
		coords = np.zeros((len(lon),3))
		coords[:,0] = R * np.cos(lat) * np.cos(lon)
		coords[:,1] = R * np.cos(lat) * np.sin(lon)
		coords[:,2] = R * np.sin(lat)
		
		return coords
	
	def setEarthSphereColour(self, new_colour):
		print("Bugged")
		print("Not implemented")
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

	def setEarthAxisColour(self, new_colour):
		self.opts['earth_axis_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['earth_axis'].set_data(color=colours.normaliseColour(new_colour))

	def setLandMassColour(self, new_colour):
		self.opts['landmass_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['landmass'].set_data(color=colours.normaliseColour(new_colour))

	def setEarthAxisVisibility(self, state):
		self.visuals['earth_axis'].visible = state

	def setLandmassVisibility(self, state):
		self.visuals['landmass'].visible = state

	def setEarthSphereVisibility(self, state):
		self.visuals['earth'].visible = state

class ParallelsGrid(BaseAsset):
	def __init__(self, parent_scene):
		self.scene = parent_scene
		self.visuals = {}
		self.requires_recompute = True
		self.eq_coords = None
		self.p_conn = None
		self.p_coords = None
		self._setDefaultOptions()
		self.compute()
		self.draw()

	def draw(self):
		self.visuals['equator'] = \
			scene.visuals.Line(self.eq_coords,
								color=colours.normaliseColour(self.opts['parallel_colour']['value']),
								antialias=self.opts['antialias']['value'],
								parent=self.scene)
		self.visuals['parallels'] = \
			scene.visuals.Line(self.p_coords,
								color=colours.normaliseColour(self.opts['parallel_colour']['value']),
								antialias=self.opts['antialias']['value'],
								connect=self.p_conn,
								parent=self.scene)

	def compute(self):
		total_len = 0
		self.eq_coords = self._genParallel(0)
		for ii in range(15, 90, self.opts['parallel_spacing']['value']):
			new_coords = self._genParallel(ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			if self.p_conn is not None:
				self.p_conn = np.vstack((self.p_conn, new_conn))
			else:
				self.p_conn = new_conn
			total_len += poly_len
			if self.p_coords is not None:
				self.p_coords = np.vstack((self.p_coords, new_coords))
			else:
				self.p_coords = new_coords
		for ii in range(15, 90, self.opts['parallel_spacing']['value']):
			new_coords = self._genParallel(-ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			self.p_conn = np.vstack((self.p_conn,new_conn))
			total_len += poly_len
			self.p_coords = np.vstack((self.p_coords, new_coords))

	def recompute(self):
		# Nothing needed for this asset
		pass

	def setCurrentECEFRotation(self, radians):
		pass

	def _genParallel(self, lat_degs):
		R = c.R_EARTH * np.cos(np.deg2rad(lat_degs))
		z = c.R_EARTH * np.sin(np.deg2rad(lat_degs))
		coords = polygons.generateCircle((0,0,z), R, (0,0,1))
		return coords

	def _createOptHelp(self):
		pass

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
										'type': 'boolean',
										'help': '',
										'callback': None}
		self._dflt_opts['equator_colour'] = {'value': (0,0,0),
											'type': 'colour',
											'help': '',
											'callback': self.setEquatorColour}
		self._dflt_opts['equator_width'] = 	{'value': 0.5,
											'type': 'number',
											'help': '',
											'callback': None}
		self._dflt_opts['parallel_spacing'] = {'value': 15,
											'type': 'number',
											'help': '',
											'callback': None}
		self._dflt_opts['parallel_colour'] = {'value': (0,0,0),
											'type': 'colour',
											'help': '',
											'callback': self.setParallelsColour}
		self._dflt_opts['parallel_width'] = {'value': 0.5,
											'type': 'number',
											'help': '',
											'callback': None}
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def setParallelsVisibility(self, state):
		self.visuals['parallels'].visible = state

	def setEquatorVisibility(self, state):
		self.visuals['equator'].visible = state

	def setEquatorColour(self, new_colour):
		self.opts['equator_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['equator'].set_data(color=colours.normaliseColour(new_colour))

	def setParallelsColour(self, new_colour):
		self.opts['parallel_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['parallels'].set_data(color=colours.normaliseColour(new_colour))

class MeridiansGrid(BaseAsset):
	def __init__(self, parent_scene):
		self.scene = parent_scene
		self.visuals = {}
		self.requires_recompute = True		
		self.m_conn = None
		self.m_coords = None
		self._setDefaultOptions()
		self.compute()
		self.draw()

	def draw(self):
		self.visuals['meridians'] = \
			scene.visuals.Line(self.m_coords,
						 		color=colours.normaliseColour(self.opts['meridian_colour']['value']),
								 antialias=self.opts['antialias']['value'],
								connect=self.m_conn,
								parent=self.scene)

	def compute(self):
		self.m_conn = None
		self.m_coords = None
		total_len = 0
		for ii in range(0, 180, self.opts['meridian_spacing']['value']):
				new_coords = self._genMeridian(ii)
				poly_len = len(new_coords)
				new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
				if self.m_conn is not None:
					self.m_conn = np.vstack((self.m_conn,new_conn))
				else:
					self.m_conn = new_conn
				total_len += poly_len
				if self.m_coords is not None:
					self.m_coords = np.vstack((self.m_coords, new_coords))
				else:
					self.m_coords = new_coords

	def recompute(self):
		if self.requires_recompute:
			rot_mat = transforms.rotAround(self.ecef_rads, pg.Z)
			new_coords = rot_mat.dot(self.m_coords.T).T
			self.visuals['meridians'].set_data(new_coords)

	def setCurrentECEFRotation(self, radians):
		self.ecef_rads = radians
		self.requires_recompute = True
		self.recompute()

	def _genMeridian(self, long_degs):
		R = c.R_EARTH * np.cos(np.deg2rad(long_degs))
		coords = polygons.generateCircle((0,0,0), R, (0,0,1))

		theta = np.linspace(0, 2.0*np.pi, 180)
		R = c.R_EARTH
		coords = np.zeros((180,3))
		coords[:,0] = R*np.cos(theta)
		coords[:,1] = np.zeros(180)
		coords[:,2] = R*np.sin(theta)
		
		rot_mat = transforms.rotAround(np.deg2rad(long_degs), pg.Z)
		coords = rot_mat.dot(coords.T).T

		return coords

	def _createOptHelp(self):
		pass

	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
										'type': 'boolean',
										'help': '',
										'callback': None}
		self._dflt_opts['meridian_spacing'] = {'value': 30,
											'type': 'number',
											'help': '',
											'callback': None}
		self._dflt_opts['meridian_colour'] = {'value': (0,0,0),
											'type': 'colour',
											'help': '',
											'callback': self.setMeridiansColour}
		self._dflt_opts['meridian_width'] = {'value': 0.5,
											'type': 'number',
											'help': '',
											'callback': None}
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def setMeridianVisibility(self, state):
		self.visuals['meridians'].visible = state

	def setMeridiansColour(self, new_colour):
		self.opts['meridian_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['meridians'].set_data(color=colours.normaliseColour(new_colour))