import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.assets import axis_indicator as axisInd

from satplot.model.geometry import transformations as transforms
from satplot.model.geometry import primgeom as pg
from satplot.model.geometry import polygons



import geopandas as gpd

from vispy import scene

import numpy as np

class Earth(BaseAsset):
	def __init__(self, canvas=None, parent=None):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.data = {}
		self.ecef_rads = 0
		self.requires_recompute = True
		self.requires_redraw = True

		self.setDefaultOptions()	
		self.addEarthSphere()
		self.addEarthAxis()
		self.addLandMass()
		self.visuals['parallels'] = ParallelsGrid(self.parent)
		self.visuals['meridians'] = MeridiansGrid(self.parent)
		self.axis_gizmo = axisInd.XYZAxis(scale=(c.R_EARTH+1500), parent=parent)
	
	def updateParentRef(self, new_parent):
		self.parent = new_parent

	def setCurrentECEFRotation(self, radians):
		self.ecef_rads = radians
		self.requires_recompute = True

	def redraw(self):
		if self.requires_redraw:
			'''DO STUFF'''
			self.requires_redraw = False

	def recompute(self):
		if self.requires_recompute:
			'''DO STUFF'''
			self.requires_recompute = False
			self.requires_redraw = True

	def addEarthSphere(self):
		self.visuals['earth'] = scene.visuals.Sphere(radius=c.R_EARTH,
										method='latitude',
										parent=self.parent,
										color=colours.normaliseColour(self.opts['earth_sphere_colour']))

	def addEarthAxis(self):
		coords = np.zeros((2,3))
		coords[0,2] = -1*(c.R_EARTH+1000)
		coords[1,2] = (c.R_EARTH+1000)
		self.visuals['earth_axis'] = scene.visuals.Line(coords,
								 		color=colours.normaliseColour(self.opts['earth_axis_colour']),
										parent=self.parent)

	def addLandMass(self):
		self.data['landmass'] = []
		gdf = gpd.read_file('data/land_boundaries/ne_110m_land.shp')
		conn = None
		total_len = 0
		all_coords = None
		for ii in gdf.index:
			polys = gdf.loc[ii].geometry
			if polys.geom_type == 'Polygon':
				coords = self._convertShapeFilePolys(polys)		
				self.data['landmass'].append(coords)
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

		self.visuals['landmass'] = scene.visuals.Line(all_coords,
													color=colours.normaliseColour(self.opts['landmass_colour']),
													antialias=self.opts['antialias'],
													connect=conn,
													parent=self.parent)
	
	def setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = True
		self._dflt_opts['draw_earth_sphere'] = True
		self._dflt_opts['earth_sphere_colour'] = (220,220,220)

		self._dflt_opts['plot_earth_axis'] = True
		self._dflt_opts['earth_axis_colour'] = (255,0,0)

		self._dflt_opts['plot_parallels'] = True

		self._dflt_opts['plot_equator'] = True

		self._dflt_opts['plot_meridians'] = True

		self._dflt_opts['plot_landmass'] = True
		self._dflt_opts['landmass_colour'] = (0,0,0)

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
	

class ParallelsGrid(BaseAsset):
	def __init__(self, parent_scene):
		self.scene = parent_scene
		self.visuals = {}
		self.eq_coords = None
		self.p_conn = None
		self.p_coords = None
		self.setDefaultOptions()
		self.recompute()
		self.redraw()

	def redraw(self):
		self.visuals['equator'] = \
			scene.visuals.Line(self.eq_coords,
								color=colours.normaliseColour(self.opts['parallel_colour']),
								antialias=self.opts['antialias'],
								parent=self.scene)
		self.visuals['parallels'] = \
			scene.visuals.Line(self.p_coords,
								color=colours.normaliseColour(self.opts['parallel_colour']),
								antialias=self.opts['antialias'],
								connect=self.p_conn,
								parent=self.scene)

	def recompute(self):
		total_len = 0
		self.eq_coords = self._genParallel(0)
		for ii in range(15, 90, self.opts['parallel_spacing']):
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
		for ii in range(15, 90, self.opts['parallel_spacing']):
			new_coords = self._genParallel(-ii)
			poly_len = len(new_coords)
			new_conn = np.array([np.arange(poly_len-1),np.arange(1,poly_len)]).T + total_len
			self.p_conn = np.vstack((self.p_conn,new_conn))
			total_len += poly_len
			self.p_coords = np.vstack((self.p_coords, new_coords))

	def _genParallel(self, lat_degs):
		R = c.R_EARTH * np.cos(np.deg2rad(lat_degs))
		z = c.R_EARTH * np.sin(np.deg2rad(lat_degs))
		coords = polygons.generateCircle((0,0,z), R, (0,0,1))
		return coords

	def _createOptHelp(self):
		pass

	def setEquatorColour(self, new_colour):
		self.opts['equator_colour'] = new_colour
		self.visuals['equator'].set_data(color=new_colour)

	def setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = True
		self._dflt_opts['equator_colour'] = (0,0,0)
		self._dflt_opts['equator_width'] = 0.5
		self._dflt_opts['parallel_spacing'] = 15
		self._dflt_opts['parallel_colour'] = (0,0,0)
		self._dflt_opts['parallel_width'] = 0.5
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

class MeridiansGrid(BaseAsset):
	def __init__(self, parent_scene):
		self.scene = parent_scene
		self.visuals = {}
		self.eq_coords = None
		self.m_conn = None
		self.m_coords = None
		self.setDefaultOptions()
		self.recompute()
		self.redraw()

	def redraw(self):
		self.visuals['meridians'] = \
			scene.visuals.Line(self.m_coords,
						 		color=colours.normaliseColour(self.opts['meridian_colour']),
								 antialias=self.opts['antialias'],
								connect=self.m_conn,
								parent=self.scene)

	def recompute(self):
		self.m_conn = None
		self.m_coords = None
		total_len = 0
		for ii in range(0, 180, self.opts['meridian_spacing']):
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
		


	def _genParallel(self, lat_degs):
		R = c.R_EARTH * np.cos(np.deg2rad(lat_degs))
		z = c.R_EARTH * np.sin(np.deg2rad(lat_degs))
		coords = polygons.generateCircle((0,0,z), R, (0,0,1))
		return coords

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

	def setDefaultOptions(self):
		self._dflt_opts = {}
		self._dflt_opts['antialias'] = True
		self._dflt_opts['meridian_spacing'] = 30
		self._dflt_opts['meridian_colour'] = (0,0,0)
		self._dflt_opts['meridian_width'] = 0.5
		self.opts = self._dflt_opts.copy()
		self._createOptHelp()