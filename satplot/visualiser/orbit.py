import numpy as np
import logging

import geopandas as gpd
import satplot.util.constants as c
import satplot.util.epoch_u as epoch_u
import satplot.visualiser.utils as visutils
import satplot.visualiser.window as window
import satplot.model.geometry.primgeom as pg
import satplot.model.geometry.transformations as transforms
import plotly.graph_objects as go
import datetime as dt
from skyfield.api import wgs84

logger = logging.getLogger(__name__)

#TODO: need to check garbage collection of actors
# ipython keeps its own references so can't check in there

epoch = dt.datetime(2000,1,1,11,58,55,816)

class OrbitVisualiser():

	def __init__(self):
		self.fig = go.Figure()
		self.fig.update_layout(scene_aspectmode='cube')
		self.fig.update_layout(scene={'xaxis_showspikes':False,
										'yaxis_showspikes':False,
										'zaxis_showspikes':False})
		# change margins
		self.fig.update_layout(margin={'l':5,
								 		'r':5,
										't':5,
										'b':5})
		# remove axes box
		self.fig.update_layout(scene={'xaxis':{'visible':False},
										'yaxis':{'visible':False},
										'zaxis':{'visible':False}})
		
		self.traces = {}
		
		self.win = None
		self.sun_dist = 10000
		
		# data
		self.sc = None
		self.orbit = None
		self.supp_orbits = []
		self.curr_index = 0
		self.landmass_points = []
		self.longitude_points = []

		self._dflt_opts = {}
		self.opts = {}
		self._setDefaultOptions()
		

	def setSource(self, orbit):
		self.orbit = orbit
		# if orbit.timespan.num_steps < self.opts['orbital_length'] * self.orbit_period:
		# 	logger.warning("Timespan has insufficient data points for the requested orbit fraction")

		self.start_index = 0
		# TODO: need to update end_index if options are changed
		self.end_index = min(len(self.orbit.timespan)-1, (self.orbit.period_steps * self.opts['orbital_length']))
		self.sun_dist = 10000

	def attachSupplementalOrbit(self, orbit):
		if self.orbit is None:
			raise AttributeError("Primary orbit not loaded")
		if orbit.timespan != self.orbit.timespan:
			raise AttributeError("Timespan of Supplemental orbit is different to Primary orbit")
		self.supp_orbits.append(orbit)

	def add3DLandMass(self, countries=False):
		# Adapted from https://community.plotly.com/t/create-earth-sphere-with-all-countries-in-plotly/79284
		# Work by user baubin
		if countries:
			gdf = gpd.read_file('data/country_boundaries/ne_110m_admin_0_countries.shp')
		else:
			gdf = gpd.read_file('data/land_boundaries/ne_110m_land.shp')

		num_traces = len(self.fig.data)
		for ii in gdf.index:
			polys = gdf.loc[ii].geometry
			if polys.geom_type == 'Polygon':
				coords = self._convertShapeFilePolys(polys)
				self.fig.add_trace(go.Scatter3d(x=coords[:,0],
												y=coords[:,1],
												z=coords[:,2],
												mode='lines',
												line={'color':f"rgb{str(self.opts['landmass_colour'])}"},
												showlegend=False,
												hoverinfo='skip'))
				self.landmass_points.append(coords)
			elif polys.geom_type == 'MultiPolygon':
				for poly in polys.geoms:
					coords = self._convertShapeFilePolys(poly)
					self.fig.add_trace(go.Scatter3d(x=coords[:,0],
													y=coords[:,1],
													z=coords[:,2],
													mode='lines',
													line={'color':f"rgb{str(self.opts['landmass_colour'])}"},
													showlegend=False,
													hoverinfo='skip'))
		end_num_traces = len(self.fig.data)
		self.traces['land_mass'] = range(num_traces, end_num_traces)

	def addEarth(self):
		if self.opts['plot_earth_sphere']:
			trace_index = visutils.plotSphere(self.fig, (0,0,0), c.R_EARTH-1, col = f"rgb{self.opts['earth_sphere_colour']}")
			self.traces['earth_sphere'] = trace_index
			self.fig.data[trace_index].contours.x.highlight = False
			self.fig.data[trace_index].contours.y.highlight = False
			self.fig.data[trace_index].contours.z.highlight = False
		
		if self.opts['plot_earth_axis']:
			trace_index = len(self.fig.data)
			self.fig.add_trace(go.Scatter3d(x=[0, 0],
											y=[0, 0],
											z=[-1*(c.R_EARTH+1000), c.R_EARTH+1000],
											mode='lines',
											line={'dash':'solid',
												'color':f"rgb{str(self.opts['earth_axis_colour'])}",
												'width':4},
											showlegend=False,
											hoverinfo='skip'))
			self.traces['axis'] = trace_index
		
		if self.opts['plot_equator']:
			self.traces['equator'] = self._addParallel(0)
		
		if self.opts['plot_parallels']:
			for ii in range(15, 90, self.opts['parallel_spacing']):
				self.traces[f'lat_{str(ii)}'] = self._addParallel(ii)
			for ii in range(15, 90, self.opts['parallel_spacing']):
				self.traces[f'lat_{str(-ii)}'] = self._addParallel(-ii)
		
		self.traces['long'] = []
		if self.opts['plot_meridians']:		
			for ii in range(0, 180, self.opts['meridian_spacing']):
				self.traces['long'].append(self._addMeridian(ii))

	def addOrbit(self):
		self.start_index = 0
		curr = max(0, self.curr_index - int(self.opts['orbital_length'] / self.orbit.period))		
		num_traces = len(self.fig.data)
		
		self.fig.add_trace(go.Scatter3d(x=self.orbit.pos[self.start_index:curr,0],
								  		y=self.orbit.pos[self.start_index:curr,1],
										z=self.orbit.pos[self.start_index:curr,2],
										mode='lines',
										line={'dash':self.opts['prim_orbit_past_style'],
											  'color':f"rgb{str(self.opts['prim_orbit_colour'])}",
											  'width':self.opts['prim_orbit_width']},
										showlegend=False))
		self.traces['past_orbit'] = num_traces
		past_text = [f'{ii}:{self.orbit.timespan.asText(ii)}' for ii in range(self.start_index,curr)]
		self.fig.data[self.traces['past_orbit']]['text'] = past_text
		self.fig.data[self.traces['past_orbit']]['hoverinfo'] = 'text'

		self.fig.add_trace(go.Scatter3d(x=self.orbit.pos[curr:self.end_index,0],
								  		y=self.orbit.pos[curr:self.end_index,1],
										z=self.orbit.pos[curr:self.end_index,2],
										mode='lines',
										line={'dash':self.opts['prim_orbit_future_style'],
											  'color':f"rgb{str(self.opts['prim_orbit_colour'])}",
											  'width':self.opts['prim_orbit_width']},
										showlegend=False))
		self.traces['future_orbit'] = num_traces+1
		fut_text = [f'{ii}:{self.orbit.timespan.asText(ii)}' for ii in range(curr, self.end_index)]
		self.fig.data[self.traces['future_orbit']]['text'] = fut_text
		self.fig.data[self.traces['future_orbit']]['hoverinfo'] = 'text'
		
		self.fig.add_trace(go.Scatter3d(x=[self.orbit.pos[self.start_index,0]],
								  		y=[self.orbit.pos[self.start_index,1]],
										z=[self.orbit.pos[self.start_index,2]],
										mode='markers',
										marker={'symbol':self.opts['prim_orbit_start_symbol'],
				  					 			'color':f"rgb{str(self.opts['prim_orbit_colour'])}",
												'size':self.opts['prim_orbit_start_symbol_size']},
										showlegend=False))
		self.traces['start_pos'] = num_traces+2
		start_text = [f'{self.start_index}:{self.orbit.timespan.asText(self.start_index)}']
		self.fig.data[self.traces['start_pos']]['text'] = start_text
		self.fig.data[self.traces['start_pos']]['hoverinfo'] = 'text'

		curr = max(0, self.curr_index - int(self.opts['orbital_length'] / self.orbit.period))
		self.fig.add_trace(go.Scatter3d(x=[self.orbit.pos[curr,0]],
								  		y=[self.orbit.pos[curr,1]],
										z=[self.orbit.pos[curr,2]],
										mode='markers',
										marker={'symbol':self.opts['prim_orbit_curr_symbol'],
				  					 			'color':f"rgb{str(self.opts['prim_orbit_colour'])}",
												'size':self.opts['prim_orbit_curr_symbol_size']},
										showlegend=False))
		self.traces['curr_pos'] = num_traces+3
		curr_text = [f'{self.curr_index}:{self.orbit.timespan.asText(self.curr_index)}']
		self.fig.data[self.traces['curr_pos']]['text'] = curr_text
		self.fig.data[self.traces['curr_pos']]['hoverinfo'] = 'text'
		
		self.fig.add_trace(go.Scatter3d(x=[self.orbit.pos[self.end_index,0]],
								  		y=[self.orbit.pos[self.end_index,1]],
										z=[self.orbit.pos[self.end_index,2]],
										mode='markers',
										marker={'symbol':self.opts['prim_orbit_end_symbol'],
				  				  				'color':f"rgb{str(self.opts['prim_orbit_colour'])}",
												'size':self.opts['prim_orbit_end_symbol_size']},
										showlegend=False))
		self.traces['end_pos'] = num_traces+4
		end_text = [f'{self.start_index}:{self.orbit.timespan.asText(self.end_index)}']
		self.fig.data[self.traces['end_pos']]['text'] = end_text
		self.fig.data[self.traces['end_pos']]['hoverinfo'] = 'text'

	def addSupplementalOrbits(self):
		self.start_index = 0
		curr = max(0, self.curr_index - int(self.opts['orbital_length'] / self.orbit.period))		
		
		self.traces['supp_past_orbit']=[]
		self.traces['supp_future_orbit']=[]
		self.traces['supp_start_pos']=[]
		self.traces['supp_curr_pos']=[]
		self.traces['supp_end_pos']=[]
		self.traces['supp_beam_cones'] =[]
		self.traces['supp_beam_caps'] =[]
		for ii, orbit in enumerate(self.supp_orbits):
			# num_traces = len(self.fig.data)
			# self.fig.add_trace(go.Scatter3d(x=orbit.pos[self.start_index:self.end_index,0],
			# 								y=orbit.pos[self.start_index:self.end_index,1],
			# 								z=orbit.pos[self.start_index:self.end_index,2],
			# 								mode='lines',
			# 								line={'dash':self.opts['supp_orbit_past_style'],
			# 									'color':f"rgb{str(self.opts['supp_orbit_colour'])}",
			# 									'width':self.opts['supp_orbit_width']},
			# 								showlegend=False))
			# self.traces['supp_past_orbit'].append(num_traces)
			# past_text = [f'{jj}:{orbit.timespan.asText(jj)}' for jj in range(self.start_index,self.end_index)]
			# self.fig.data[self.traces['supp_past_orbit'][ii]]['text'] = past_text
			# self.fig.data[self.traces['supp_past_orbit'][ii]]['hoverinfo'] = 'text'

			# num_traces = len(self.fig.data)
			# self.fig.add_trace(go.Scatter3d(x=orbit.pos[curr:self.end_index,0],
			# 								y=orbit.pos[curr:self.end_index,1],
			# 								z=orbit.pos[curr:self.end_index,2],
			# 								mode='lines',
			# 								line={'dash':self.opts['supp_orbit_future_style'],
			# 									'color':f"rgb{str(self.opts['supp_orbit_colour'])}",
			# 									'width':self.opts['supp_orbit_width']},
			# 								showlegend=False))
			# self.traces['supp_future_orbit'].append(num_traces)
			# fut_text = [f'{jj}:{orbit.timespan.asText(jj)}' for jj in range(curr, self.end_index)]
			# self.fig.data[self.traces['supp_future_orbit'][ii]]['text'] = fut_text
			# self.fig.data[self.traces['supp_future_orbit'][ii]]['hoverinfo'] = 'text'
			
			# num_traces = len(self.fig.data)
			# self.fig.add_trace(go.Scatter3d(x=[orbit.pos[self.start_index,0]],
			# 								y=[orbit.pos[self.start_index,1]],
			# 								z=[orbit.pos[self.start_index,2]],
			# 								mode='markers',
			# 								marker={'symbol':self.opts['supp_orbit_start_symbol'],
			# 										'color':f"rgb{str(self.opts['supp_orbit_colour'])}",
			# 										'size':self.opts['supp_orbit_start_symbol_size']},
			# 								showlegend=False))
			# self.traces['supp_start_pos'].append(num_traces)
			# start_text = [f'{self.start_index}:{orbit.timespan.asText(self.start_index)}']
			# self.fig.data[self.traces['supp_start_pos'][ii]]['text'] = start_text
			# self.fig.data[self.traces['supp_start_pos'][ii]]['hoverinfo'] = 'text'

			num_traces = len(self.fig.data)
			curr = max(0, self.curr_index - int(self.opts['orbital_length'] / orbit.period))
			self.fig.add_trace(go.Scatter3d(x=[orbit.pos[curr,0]],
											y=[orbit.pos[curr,1]],
											z=[orbit.pos[curr,2]],
											mode='markers',
											marker={'symbol':self.opts['supp_orbit_curr_symbol'],
													'color':f"rgb{str(self.opts['supp_orbit_colour'])}",
													'size':self.opts['supp_orbit_curr_symbol_size']},
											showlegend=False))
			self.traces['supp_curr_pos'].append(num_traces)
			curr_text = str(orbit.sat)
			print(curr_text)
			self.fig.data[self.traces['supp_curr_pos'][ii]]['text'] = curr_text
			self.fig.data[self.traces['supp_curr_pos'][ii]]['hoverinfo'] = 'text'
			
			# num_traces = len(self.fig.data)
			# self.fig.add_trace(go.Scatter3d(x=[orbit.pos[self.end_index,0]],
			# 								y=[orbit.pos[self.end_index,1]],
			# 								z=[orbit.pos[self.end_index,2]],
			# 								mode='markers',
			# 								marker={'symbol':self.opts['supp_orbit_end_symbol'],
			# 										'color':f"rgb{str(self.opts['supp_orbit_colour'])}",
			# 										'size':self.opts['supp_orbit_end_symbol_size']},
			# 								showlegend=False))
			# self.traces['supp_end_pos'].append(num_traces)
			# end_text = [f'{self.start_index}:{orbit.timespan.asText(self.end_index)}']
			# self.fig.data[self.traces['supp_end_pos'][ii]]['text'] = end_text
			# self.fig.data[self.traces['supp_end_pos'][ii]]['hoverinfo'] = 'text'

			cone_index, cap_index = visutils.plotCone(self.fig,
														orbit.pos[curr],
														np.linalg.norm(orbit.pos[curr]) - c.R_EARTH,
														-1*pg.unitVector(orbit.pos[curr]),
														62.9*2,
														col = f"rgb{self.opts['supp_orbit_colour']}",
														alpha=0.2)
			self.traces['supp_beam_cones'].append(cone_index)
			self.traces['supp_beam_caps'].append(cap_index)

	def updateOrbit(self):
		curr = max(0, self.curr_index - int(self.opts['orbital_length'] / self.orbit.period))
		rot_rad = self._getCurrentECEFRotation(curr)
		# rot_deg = 0
		rot_mat = transforms.rotAround(rot_rad, pg.Z)
		print(f"pos indices:{self.start_index}->{curr}->{self.end_index}")
		
		self.fig.data[self.traces['past_orbit']].x = self.orbit.pos[self.start_index:curr,0]
		self.fig.data[self.traces['past_orbit']].y = self.orbit.pos[self.start_index:curr,1]
		self.fig.data[self.traces['past_orbit']].z = self.orbit.pos[self.start_index:curr,2]
		self.fig.data[self.traces['future_orbit']].x = self.orbit.pos[curr:self.end_index,0]
		self.fig.data[self.traces['future_orbit']].y = self.orbit.pos[curr:self.end_index,1]
		self.fig.data[self.traces['future_orbit']].z = self.orbit.pos[curr:self.end_index,2]
		self.fig.data[self.traces['curr_pos']].x = [self.orbit.pos[curr,0]]
		self.fig.data[self.traces['curr_pos']].y = [self.orbit.pos[curr,1]]
		self.fig.data[self.traces['curr_pos']].z = [self.orbit.pos[curr,2]]
		past_text = [f'{ii}:{self.orbit.timespan.asText(ii)}' for ii in range(self.start_index,curr)]
		fut_text = [f'{ii}:{self.orbit.timespan.asText(ii)}' for ii in range(curr, self.end_index)]
		curr_text = [f'{curr}:{self.orbit.timespan.asText(curr)}']
		self.fig.data[self.traces['future_orbit']]['text'] = fut_text
		self.fig.data[self.traces['future_orbit']]['hoverinfo'] = 'text'
		self.fig.data[self.traces['past_orbit']]['text'] = past_text
		self.fig.data[self.traces['past_orbit']]['hoverinfo'] = 'text'
		self.fig.data[self.traces['curr_pos']]['text'] = curr_text
		self.fig.data[self.traces['curr_pos']]['hoverinfo'] = 'text'

		for ii, orbit in enumerate(self.supp_orbits):
			# self.fig.data[self.traces['supp_past_orbit'][ii]].x = orbit.pos[self.start_index:self.end_index,0]
			# self.fig.data[self.traces['supp_past_orbit'][ii]].y = orbit.pos[self.start_index:self.end_index,1]
			# self.fig.data[self.traces['supp_past_orbit'][ii]].z = orbit.pos[self.start_index:self.end_index,2]
			# self.fig.data[self.traces['supp_future_orbit'][ii]].x = orbit.pos[curr:self.end_index,0]
			# self.fig.data[self.traces['supp_future_orbit'][ii]].y = orbit.pos[curr:self.end_index,1]
			# self.fig.data[self.traces['supp_future_orbit'][ii]].z = orbit.pos[curr:self.end_index,2]
			self.fig.data[self.traces['supp_curr_pos'][ii]].x = [orbit.pos[curr,0]]
			self.fig.data[self.traces['supp_curr_pos'][ii]].y = [orbit.pos[curr,1]]
			self.fig.data[self.traces['supp_curr_pos'][ii]].z = [orbit.pos[curr,2]]
			past_text = [f'{jj}:{self.orbit.timespan.asText(jj)}' for jj in range(self.start_index,self.end_index)]
			fut_text = [f'{jj}:{self.orbit.timespan.asText(jj)}' for jj in range(curr, self.end_index)]
			curr_text = [orbit.sat]
			# self.fig.data[self.traces['supp_future_orbit'][ii]]['text'] = fut_text
			# self.fig.data[self.traces['supp_future_orbit'][ii]]['hoverinfo'] = 'text'
			# self.fig.data[self.traces['supp_past_orbit'][ii]]['text'] = past_text
			# self.fig.data[self.traces['supp_past_orbit'][ii]]['hoverinfo'] = 'text'
			self.fig.data[self.traces['supp_curr_pos'][ii]]['text'] = curr_text
			self.fig.data[self.traces['supp_curr_pos'][ii]]['hoverinfo'] = 'text'

		if self.opts['plot_meridians']:
			for ii, trace_index in enumerate(self.traces['long']):
				meridian = self.longitude_points[ii]
				new_coords = rot_mat.dot(meridian.T).T
				self.fig.data[trace_index].x = new_coords[:,0]
				self.fig.data[trace_index].y = new_coords[:,1]
				self.fig.data[trace_index].z = new_coords[:,2]

		if self.opts['plot_landmass']:
			for ii, trace_index in enumerate(self.traces['land_mass']):
				landmass = self.landmass_points[ii]
				new_coords = rot_mat.dot(landmass.T).T
				self.fig.data[trace_index].x = new_coords[:,0]
				self.fig.data[trace_index].y = new_coords[:,1]
				self.fig.data[trace_index].z = new_coords[:,2]

	def addUmbra(self):
		shadow_point = -self.sun_dist * pg.unitVector(self.orbit.sun[self.curr_index])

		p0 = np.array([0,0,0])
		p1 = shadow_point
		R = c.R_EARTH
		v_mag = np.linalg.norm(p1-p0)
		v = pg.unitVector(p1-p0)
		not_v = np.array([1,0,0])
		if(v == not_v).all():
			not_v = np.array([0,1,0])
		n1 = pg.unitVector(np.cross(v, not_v))
		n2 = pg.unitVector(np.cross(v, n1))

		t = np.linspace(0,v_mag,2)
		theta = np.linspace(0, 2*np.pi, 99)
		rsample = np.linspace(0,R,2)
		t, theta2 = np.meshgrid(t,theta)
		rsample, theta = np.meshgrid(rsample, theta)
		X,Y,Z = [p0[i] + v[i] * t + R * np.sin(theta2) * n1[i] + R * np.cos(theta) * n2[i] for i in [0, 1, 2]]
		X2,Y2,Z2 = [p0[i] + v[i]*v_mag + rsample[i] * np.sin(theta) * n1[i] + rsample[i] * np.cos(theta) * n2[i] for i in [0, 1, 2]]
		col=f"rgb{str(self.opts['umbra_colour'])}"
		num_traces = len(self.fig.data)

		self.fig.add_surface(x=X,
					   		y=Y,
							z=Z,
							colorscale=[[0, col], [1, col]],
							opacity=self.opts['umbra_opacity'],
							showlegend=False,
							lighting=dict(diffuse=0.1),
							hoverinfo='skip',
							showscale=False)
		self.traces['umbra_tube'] = num_traces

		self.fig.add_surface(x=X2,
					   		y=Y2,
							z=Z2,
							colorscale=[[0, col], [1, col]],
							opacity=self.opts['umbra_opacity'],
							showlegend=False,
							lighting=dict(diffuse=0.1),
							hoverinfo='skip',
							showscale=False)
		self.traces['umbra_cap'] = num_traces+1
		
		self.fig.data[self.traces['umbra_tube']].contours.x.highlight = False
		self.fig.data[self.traces['umbra_tube']].contours.y.highlight = False
		self.fig.data[self.traces['umbra_tube']].contours.z.highlight = False
		self.fig.data[self.traces['umbra_cap']].contours.x.highlight = False
		self.fig.data[self.traces['umbra_cap']].contours.y.highlight = False
		self.fig.data[self.traces['umbra_cap']].contours.z.highlight = False

		trace_index = visutils.plotSphere(self.fig, -1.5*shadow_point, 500, col=f"rgb{str(self.opts['sun_colour'])}")
		self.traces['sun'] = trace_index

		self.fig.update_layout(scene={'xaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})
		self.fig.update_layout(scene={'yaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})
		self.fig.update_layout(scene={'zaxis':{'range':[-1*(v_mag+c.R_EARTH/2), (v_mag+c.R_EARTH/2)]}})


	def openWindow(self):
		self.win = window.FigureViewer(self.fig)

	def updateWindow(self):
		self.updateOrbit()
		self.fig.update_layout(coloraxis_showscale=False)
		self.win.update()

	def getTrace(self, trace_name):
		trace_index = None
		try:
			trace_index = self.traces[trace_name]
		except KeyError:
			print(f"{trace_name} is not a valid trace.")
			print("This visualiser has the following traces:")
			for key in self.traces.keys():
				print(f"\t{key}")
		return self.fig.data[trace_index]

	def getTraceIndex(self, trace_name):
		trace_index = None
		try:
			trace_index = self.traces[trace_name]
		except KeyError:
			print(f"{trace_name} is not a valid trace.")
			print("This visualiser has the following traces:")
			for key in self.traces.keys():
				print(f"\t{key}")
		return trace_index

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

	def _addParallel(self, lat_degs):
		trace_index = len(self.fig.data)
		long = np.linspace(0, 2.0*np.pi, 180)
		R = c.R_EARTH * np.cos(np.deg2rad(lat_degs))
		x = R*np.cos(long)
		y = R*np.sin(long)
		z = c.R_EARTH*np.ones(180)*np.sin(np.deg2rad(lat_degs))
		self.fig.add_trace(go.Scatter3d(x=x,
										y=y,
										z=z,
										mode='lines',
										line={'dash':self.opts['parallel_style'],
												'color':f"rgb{str(self.opts['parallel_colour'])}",
												'width':self.opts['parallel_width']},
										hoverinfo='skip',
										showlegend=False))
		return trace_index

	def _addMeridian(self, long_degs):
		trace_index = len(self.fig.data)
		theta = np.linspace(0, 2.0*np.pi, 180)
		R = c.R_EARTH
		coords = np.zeros((180,3))
		coords[:,0] = R*np.cos(theta)
		coords[:,1] = np.zeros(180)
		coords[:,2] = R*np.sin(theta)
		
		rot_mat = transforms.rotAround(np.deg2rad(long_degs), pg.Z)
		coords = rot_mat.dot(coords.T).T

		self.fig.add_trace(go.Scatter3d(x=coords[:,0],
										y=coords[:,1],
										z=coords[:,2],
										mode='lines',
										line={'dash':self.opts['meridian_style'],
												'color':f"rgb{str(self.opts['meridian_colour'])}",
												'width':self.opts['meridian_width']},
										hoverinfo='skip',
										showlegend=False))
		self.longitude_points.append(coords)
		return trace_index

	def _getCurrentECEFRotation(self, index):
		topos = wgs84.latlon(0,0)
		t = self.orbit.timespan.asSkyfield(index)
		nullisland_curr = topos.at(t).xyz.km
		rot_rad = np.arctan2(nullisland_curr[1], nullisland_curr[0])
		return rot_rad
	
	def _createOptHelp(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['placeholder'] = 'No help exists yet'
				# self.opts_help['color'] = "Colour to be used for orbit trajectory. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['color'])
				# self.opts_help['pos_marker'] = "Marker to be used for indexed orbit position. dflt: '{opt}'. fmt: matplotlib marker string".format(opt=self._dflt_opts['pos_marker'])
				# self.opts_help['marker_size'] = "Marker size to be used for indexed orbit position. dflt: '{opt}'. fmt: int".format(opt=self._dflt_opts['marker_size'])
				# self.opts_help['umbra_color'] = "Color to be used with the umbra cylinder. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['umbra_color'])
				# self.opts_help['umbra_edge'] = "Color to be used with the umbra edge. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['umbra_color'])
				# self.opts_help['orbital_length'] = "Multiplier for how many orbital periods are to be plotted. dflt: '{opt}'. fmt: float".format(opt=self._dflt_opts['orbital_length'])
				# self.opts_help['x_units'] = "Unit to be displayed on x axis. dflt: '{opt}'.".format(opt=self._dflt_opts['x_units'])
				# self.opts_help['y_units'] = "Unit to be displayed on y axis. dflt: '{opt}'.".format(opt=self._dflt_opts['y_units'])
				# self.opts_help['z_units'] = "Unit to be displayed on z axis. dflt: '{opt}'.".format(opt=self._dflt_opts['z_units'])
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.setDefaultOptions()

			if self.opts_help.keys() != self._dflt_opts.keys():
				logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))

	def _setDefaultOptions(self):
		
		self._dflt_opts['orbital_length'] = 1

		self._dflt_opts['prim_orbit_colour'] = (0,0,255)
		self._dflt_opts['prim_orbit_width'] = 4
		self._dflt_opts['prim_orbit_start_symbol'] = 'x'
		self._dflt_opts['prim_orbit_start_symbol_size'] = 2
		self._dflt_opts['prim_orbit_curr_symbol'] = 'circle'
		self._dflt_opts['prim_orbit_curr_symbol_size'] = 2
		self._dflt_opts['prim_orbit_end_symbol'] = 'diamond'
		self._dflt_opts['prim_orbit_end_symbol_size'] = 2
		self._dflt_opts['prim_orbit_past_style'] = 'solid'
		self._dflt_opts['prim_orbit_future_style'] = 'dash'
		
		self._dflt_opts['supp_orbit_colour'] = (0,255,0)
		self._dflt_opts['supp_orbit_width'] = 2
		self._dflt_opts['supp_orbit_start_symbol'] = 'x'
		self._dflt_opts['supp_orbit_start_symbol_size'] = 1
		self._dflt_opts['supp_orbit_curr_symbol'] = 'circle'
		self._dflt_opts['supp_orbit_curr_symbol_size'] = 1.75 
		self._dflt_opts['supp_orbit_end_symbol'] = 'diamond'
		self._dflt_opts['supp_orbit_end_symbol_size'] = 1
		self._dflt_opts['supp_orbit_past_style'] = 'solid'
		self._dflt_opts['supp_orbit_future_style'] = 'dash'

		self._dflt_opts['plot_earth_sphere'] = True
		self._dflt_opts['earth_sphere_colour'] = (220,220,220)

		self._dflt_opts['plot_landmass'] = True
		self._dflt_opts['landmass_colour'] = (0,0,0)

		self._dflt_opts['plot_earth_axis'] = True
		self._dflt_opts['earth_axis_colour'] = (255,0,0)
		self._dflt_opts['earth_axis_style'] = 'solid'
		
		self._dflt_opts['umbra_colour'] = (0,0,0)
		self._dflt_opts['umbra_opacity'] = 0.1
		self._dflt_opts['sun_colour'] = (255,255,0)
		
		self._dflt_opts['plot_equator'] = True

		self._dflt_opts['plot_parallels'] = True
		self._dflt_opts['parallel_spacing'] = 15
		self._dflt_opts['parallel_colour'] = (0,0,0)
		self._dflt_opts['parallel_width'] = 0.5
		self._dflt_opts['parallel_style'] = 'solid'
		
		self._dflt_opts['plot_meridians'] = True
		self._dflt_opts['meridian_spacing'] = 30
		self._dflt_opts['meridian_colour'] = (0,0,0)
		self._dflt_opts['meridian_width'] = 0.5
		self._dflt_opts['meridian_style'] = 'solid'

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()