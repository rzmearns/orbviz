import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset, SimpleAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons
import satplot.model.timespan as timespan

import geopandas as gpd
from skyfield.api import wgs84

from vispy import scene, color
from vispy.visuals import transforms as vTransforms

import numpy as np

class Earth(BaseAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)
						
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		# These callbacks need to be set after asset creation as the option dict is populated during draw()
		self.opts['plot_meridians']['callback'] = self.assets['meridians'].setVisibility
		self.opts['plot_parallels']['callback'] = self.assets['parallels'].setVisibility
		self.opts['plot_equator']['callback'] = self.assets['parallels'].setVisibility

		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Earth'		
		self.data['ecef_rads'] = 0
		self.data['datetimes'] = None
		# earth axis data
		self.data['ea_coords'] = np.zeros((2,3))
		self.data['ea_coords'][0,2] = -1*(c.R_EARTH+1000)
		self.data['ea_coords'][1,2] = (c.R_EARTH+1000)

		# landmass data
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
		self.data['landmass_conn'] = conn

		# rotation data
		self.data['nullisland_topos'] = wgs84.latlon(0,0)

	def setSource(self, *args, **kwargs):		
		if type(args[0]) is not timespan.TimeSpan:
			# args[0] assumed to be timespan
			raise TypeError
		# TODO: add capability to produce array of skyfields)
		times = []
		for ii in range(len(args[0])):
			times.append(args[0].asSkyfield(ii))
		self.data['datetimes'] = np.asarray(times)
		for asset in self.assets.values():
			asset.setSource(self.data['datetimes'])

	def _instantiateAssets(self):
		self.assets['parallels'] = ParallelsGrid(v_parent=self.data['v_parent'])
		self.assets['meridians'] = MeridiansGrid(v_parent=self.data['v_parent'])

	def _createVisuals(self):
		# Earth Sphere
		self.visuals['earth_sphere'] = scene.visuals.Sphere(radius=c.R_EARTH,
								method='latitude',
								parent=None,
								color=colours.normaliseColour(self.opts['earth_sphere_colour']['value']))
		# Earth Axis
		self.visuals['earth_axis'] = scene.visuals.Line(self.data['ea_coords'],
								 		color=colours.normaliseColour(self.opts['earth_axis_colour']['value']),
										parent=None)
		# Landmass
		self.visuals['landmass'] = scene.visuals.Line(self.data['landmass'],
													color=colours.normaliseColour(self.opts['landmass_colour']['value']),
													antialias=self.opts['antialias']['value'],
													connect=self.data['landmass_conn'],
													parent=None)

	# Override BaseAsset.updateIndex()
	def updateIndex(self, index):
		self.data['curr_index'] = index
		nullisland_curr = self.data['nullisland_topos'].at(self.data['datetimes'][self.data['curr_index']]).xyz.km
		rot_rad = np.arctan2(nullisland_curr[1], nullisland_curr[0])
		self.data['ecef_rads'] = rot_rad
		for asset in self.assets.values():
			if isinstance(asset,BaseAsset):
				asset.updateIndex(index)
		self.requires_recompute = True
		self.recompute()

	def recompute(self):
		if self.first_draw:
			self.first_draw = False
		if self.requires_recompute:
			R = transforms.rotAround(self.data['ecef_rads'], pg.Z)
			new_coords = R.dot(self.data['landmass'].T).T
			self.visuals['landmass'].set_data(new_coords)
			for asset in self.assets.values():
				asset.setTransform(rotation=R)
			

			self.requires_recompute = False
	
	def _setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = {'value': True,
								  		'type': 'boolean',
										'help': '',
												'callback': None}
		self._dflt_opts['plot_earth'] = {'value': True,
										  		'type': 'boolean',
												'help': '',
												'callback': self.setVisibility}
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

	#----- OPTIONS CALLBACKS -----#
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
		self.visuals['earth_sphere'].visible = state

	#----- HELPER FUNCTIONS -----#
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


class ParallelsGrid(SimpleAsset):
	def __init__(self,name=None, v_parent=None):
		super().__init__(name, v_parent)
		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()
		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Parallels'		
		self.data['init_eq_coords'] = self._genParallel(0)
		self.data['init_p_coords'] = None
		self.data['p_conn'] = None
		total_len = 0
		for ii in range(15, 90, self.opts['parallel_spacing']['value']):
			new_coords = self._genParallel(ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			if self.data['p_conn'] is not None:
				self.data['p_conn'] = np.vstack((self.data['p_conn'], new_conn))
			else:
				self.data['p_conn'] = new_conn
			total_len += poly_len
			if self.data['init_p_coords'] is not None:
				self.data['init_p_coords'] = np.vstack((self.data['init_p_coords'], new_coords))
			else:
				self.data['init_p_coords'] = new_coords
		for ii in range(15, 90, self.opts['parallel_spacing']['value']):
			new_coords = self._genParallel(-ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			self.data['p_conn'] = np.vstack((self.data['p_conn'],new_conn))
			total_len += poly_len
			self.data['init_p_coords'] = np.vstack((self.data['init_p_coords'], new_coords))

	def setSource(self, *args, **kwargs):
		# No updating, so no source
		pass

	def _instantiateAssets(self):
		# No sub assets
		pass

	def _createVisuals(self):
		self.visuals['equator'] = \
			scene.visuals.Line(self.data['init_eq_coords'],
								color=colours.normaliseColour(self.opts['parallel_colour']['value']),
								antialias=self.opts['antialias']['value'],
								parent=None)
		self.visuals['parallels'] = \
			scene.visuals.Line(self.data['init_p_coords'],
								color=colours.normaliseColour(self.opts['parallel_colour']['value']),
								antialias=self.opts['antialias']['value'],
								connect=self.data['p_conn'],
								parent=None)

	def setTransform(self, pos=(0,0,0), rotation=np.eye(3)):
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
	
	#----- OPTIONS CALLBACKS -----#
	def setParallelsVisibility(self, state):
		if state:
			self.visuals['parallels'].parent = self.data['v_parent']
		else:
			self.visuals['parallels'].parent = None

	def setEquatorVisibility(self, state):
		if state:
			self.visuals['equator'].parent = self.data['v_parent']
		else:
			self.visuals['equator'].parent = None

	def setEquatorColour(self, new_colour):
		self.opts['equator_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['equator'].set_data(color=colours.normaliseColour(new_colour))

	def setParallelsColour(self, new_colour):
		self.opts['parallel_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['parallels'].set_data(color=colours.normaliseColour(new_colour))

	#----- HELPER FUNCTIONS -----#
	def _genParallel(self, lat_degs):
		R = c.R_EARTH * np.cos(np.deg2rad(lat_degs))
		z = c.R_EARTH * np.sin(np.deg2rad(lat_degs))
		coords = polygons.generateCircle((0,0,z), R, (0,0,1))
		return coords
	

class MeridiansGrid(SimpleAsset):
	def __init__(self, name=None, v_parent=None):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self._instantiateAssets()
		self._createVisuals()

		self.attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'Meridians'		
		self.data['init_m_coords'] = None
		self.data['m_conn'] = None
		total_len = 0
		for ii in range(0, 180, self.opts['meridian_spacing']['value']):
			new_coords = self._genMeridian(ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			if self.data['m_conn'] is not None:
				self.data['m_conn'] = np.vstack((self.data['m_conn'],new_conn))
			else:
				self.data['m_conn'] = new_conn
			total_len += poly_len
			if self.data['init_m_coords'] is not None:
				self.data['init_m_coords'] = np.vstack((self.data['init_m_coords'], new_coords))
			else:
				self.data['init_m_coords'] = new_coords

	def setSource(self, *args, **kwargs):		
		pass

	def _instantiateAssets(self):
		# No sub assets
		pass

	def _createVisuals(self):
		self.visuals['meridians'] = \
			scene.visuals.Line(self.data['init_m_coords'],
						 		color=colours.normaliseColour(self.opts['meridian_colour']['value']),
								 antialias=self.opts['antialias']['value'],
								connect=self.data['m_conn'],
								parent=None)

		self.setTransform()

	def setTransform(self, pos=(0,0,0), rotation=np.eye(3)):
		T = np.eye(4)
		T[0:3,0:3] = rotation
		T[0:3,3] = np.asarray(pos).reshape(-1,3)
		self.visuals['meridians'].transform = vTransforms.linear.MatrixTransform(T.T)

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

	#----- OPTIONS CALLBACKS -----#

	def setMeridianVisibility(self, state):
		if state:
			self.visuals['meridians'].parent = self.data['v_parent']
		else:
			self.visuals['meridians'].parent = None

	def setMeridiansColour(self, new_colour):
		self.opts['meridian_colour']['value'] = colours.normaliseColour(new_colour)
		self.visuals['meridians'].set_data(color=colours.normaliseColour(new_colour))

	#----- HELPER FUNCTIONS -----#
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