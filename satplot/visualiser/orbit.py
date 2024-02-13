import numpy as np
import logging

import satplot.visualiser.utils as vis_utils
import satplot.visualiser.basevisualiser as basevisualiser
import satplot.util.constants as consts
import satplot.visualiser.Assets as assets
import satplot.model.geometry.primgeom as pg

import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

#TODO: need to check garbage collection of actors
# ipython keeps its own references so can't check in there


class OrbitVisualiser(basevisualiser.Base):
	"""Visualiser for an orbit created within satplot
	
	"""
	def __init__(self, subplot=False, subplot_args=[None, 111]):
		"""Creates visualiser instance
		
		Creates a new matplotlib figure and 3d axes within it.
		"""
		if not subplot:
			self.label_str = 'orbit'			
			vis_utils.createFigure(self.label_str, 'Orbit', three_dim=True)
		else:
			self.label_str = subplot_args[0]
			vis_utils.createFigure(self.label_str, 'Orbit', three_dim=True, subplot_pos=subplot_args[1])

		self.subplot_pos = subplot_args[1]
		self.setDefaultOptions()
		self.fig = vis_utils.findFigure(self.label_str)
		print(f"self.fig:{self.fig}")
		self.ax = vis_utils.findAxes(self.label_str, self.subplot_pos)
		
		print(f"self.ax:{self.ax}")
		self.orbit_points = None
		self.orbit_vel = None
		self.index = 0
		self.actors = {}
		self.source = None
		self.sc_source = None

		self.earth = assets.Earth(self, self.ax)
		self.actors['earth'] = self.earth.draw()
		# self.sun_dist = np.linalg.norm(self.orbit_points[0, :]) * 1.5
		self.sun_dist = 10000
		self.sun = assets.Sun(self, self.ax, self.sun_dist)
		print("setting limit")
		self.ax.set_xlim([-7000, 7000])
		vis_utils.squareAxes(self.label_str, subplot_pos=self.subplot_pos)

	def setDefaultOptions(self):
		""" Sets the default options for the orbit_visualiser
		
		"""
		self._dflt_opts = {}
		
		self._dflt_opts['color'] = 'b'
		self._dflt_opts['pos_marker'] = 'o'
		self._dflt_opts['start_marker'] = 'x'
		self._dflt_opts['end_marker'] = '>'
		self._dflt_opts['marker_size'] = 20		
		self._dflt_opts['umbra_color'] = np.asarray([110, 110, 110, 128]) / 256
		self._dflt_opts['umbra_edge'] = 'k'
		self._dflt_opts['orbital_length'] = 1
		self._dflt_opts['x_units'] = 'x [km]'
		self._dflt_opts['y_units'] = 'y [km]'
		self._dflt_opts['z_units'] = 'z [km]'

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def setSource(self, source):
		""" Sets source for orbit visualiser
		
		Source should be taken from an orbit class, currently set manually
		
		Parameters
		----------
		source : {(n,3) ndarray}
		"""
		# Set source to orbit class
		# TODO: check source is an instance of orbit
		self.source = source
		self.orbit_points = source.pos
		# self.orbit_points = source
		# pull this from Orbit class once instituted
		self.sun_dist = np.linalg.norm(self.orbit_points[0, :]) * 1.5
		self.sun_rad = 2 * np.deg2rad(0.5) * self.sun_dist
		# Need to pull this from orbit class once instituted
		self.orbit_period = source.steps_orbital_period

		if source.timespan.num_steps < self.opts['orbital_length'] * self.orbit_period:
			logger.warning("Timespan has insufficient data points for the requested orbit fraction")
		
		self.orbit_vel = source.vel
		# self.sun = source.sun / np.linalg.norm(source.sun, axis=1)[:, None] * self.sun_dist

	def setSpacecraftSource(self, source):
		"""Sets spacecraft source for visualiser
		
		Uses spacecraft source for rotating the spacecraft gizmo
		
		Parameters
		----------
		source : {satplot.Spacecraft}
		"""
		self.sc_source = source
		self.gizmo = assets.Gizmo(self, self.ax, 900)

	def plotOrbit(self):
		""" Plots orbital trajectory from indexed position for an orbital period
		
		The length of the trajectory plotted can be set via the options 'orbital_length'
		"""
		if 'fut_trajectory' in self.actors.keys():
			self.actors['fut_trajectory'][0].remove()
			del self.actors['fut_trajectory']
		if 'past_trajectory' in self.actors.keys():			
			self.actors['past_trajectory'][0].remove()
			del self.actors['past_trajectory']
		start = 0
		curr = max(0, self.index - int(self.opts['orbital_length'] / self.orbit_period))
		end = min(len(self.source.timespan), (self.source.steps_orbital_period * self.opts['orbital_length']))
		print(f"{start}->{end}")
		self.actors['fut_trajectory'] = self.ax.plot(self.orbit_points[curr:end, 0],
											self.orbit_points[curr:end, 1],
											self.orbit_points[curr:end, 2], color=self.opts['color'])  # noqa: E126
		self.actors['past_trajectory'] = self.ax.plot(self.orbit_points[start:curr, 0],
											self.orbit_points[start:curr, 1],
											self.orbit_points[start:curr, 2], color=self.opts['color'], linestyle='dotted')  # noqa: E126


	def plotPos(self, gizmo=True):
		""" Plots index position from attached orbit object
		
		Parameters
		----------
		gizmo : {bool}, optional
			Spacecraft gizmo (the default is True, which will display the gizmo)
		"""
		
		if not gizmo:
			if 'pos' in self.actors.keys():
				self.actors['pos'].remove()
				del self.actors['pos']

			self.actors['pos'] = self.ax.scatter(self.orbit_points[self.index, 0],
									self.orbit_points[self.index, 1],
									self.orbit_points[self.index, 2],  # noqa: E126
									marker=self.opts['pos_marker'], 
									s=self.opts['marker_size'],
									color=self.opts['color'])
		else:
			if 'gizmo' in self.actors.keys():
				self.actors['gizmo'].remove()
				del self.actors['gizmo']

			self.gizmo.transform(self.sc_source.pointing[self.index], self.sc_source.orbit.pos[self.index])
			self.actors['gizmo'] = self.gizmo.draw()

	def plotStart(self):
		""" Plots index position from attached orbit object
		
		Parameters
		----------
		gizmo : {bool}, optional
			Spacecraft gizmo (the default is True, which will display the gizmo)
		"""
		
		if 'start' in self.actors.keys():
			self.actors['start'].remove()
			del self.actors['start']

		self.actors['start'] = self.ax.scatter(self.orbit_points[0, 0],
								self.orbit_points[0, 1],
								self.orbit_points[0, 2],  # noqa: E126
								marker=self.opts['start_marker'], 
								s=self.opts['marker_size'],
								color=self.opts['color'])

	def plotEnd(self):
		""" Plots index position from attached orbit object
		
		Parameters
		----------
		gizmo : {bool}, optional
			Spacecraft gizmo (the default is True, which will display the gizmo)
		"""
		
		if 'end' in self.actors.keys():
			self.actors['end'].remove()
			del self.actors['end']

		self.actors['end'] = self.ax.scatter(self.orbit_points[-1, 0],
								self.orbit_points[-1, 1],
								self.orbit_points[-1, 2],  # noqa: E126
								marker=self.opts['end_marker'], 
								s=self.opts['marker_size'],
								color=self.opts['color'])

	def drawUmbra(self):
		""" Draws earth umbra in anti-sun direction, determined by sun location in attached orbit object
		
		Due to matplotlib z order issues, umbra will not display properly at some orientations.
		"""
		shadow_color = self.opts['umbra_color']
		shadow_edge = self.opts['umbra_edge']

		if 'umbra' in self.actors.keys():
			logger.debug("Removing umbra from orbit plot")
			self.actors['umbra'].remove()
			self.actors['umbra_cap1'].remove()
			self.actors['umbra_cap2'].remove()
			del self.actors['umbra']
			del self.actors['umbra_cap1']
			del self.actors['umbra_cap2']

		shadow_point = - self.sun_dist * pg.unitVector(self.source.sun[self.index])

		origin = np.array([0, 0, 0])
		# axis and radius
		p0 = origin
		p1 = shadow_point
		# print(self.source.sun[self.index])
		# print(shadow_point)
		# TODO: need to pull radius from orbit central body
		R = consts.R_EARTH
		# vector in direction of axis
		v = p1 - p0
		# find magnitude of vector
		mag = np.linalg.norm(v)
		# unit vector in direction of axis
		v = v / mag
		# make some vector not in the same direction as v
		not_v = np.array([1, 0, 0])
		if (v == not_v).all():
			not_v = np.array([0, 1, 0])
		# make vector perpendicular to v
		n1 = np.cross(v, not_v)
		# normalize n1
		n1 /= np.linalg.norm(n1)
		# make unit vector perpendicular to v and n1
		n2 = np.cross(v, n1)
		# surface ranges over t from 0 to length of axis and 0 to 2*pi
		t = np.linspace(0, mag, 2)
		theta = np.linspace(0, 2 * np.pi, 99)
		rsample = np.linspace(0, R, 2)
		# use meshgrid to make 2d arrays
		t, theta2 = np.meshgrid(t, theta)
		rsample, theta = np.meshgrid(rsample, theta)
		logger.debug("Adding umbra to orbit plot")
		# Tube
		X, Y, Z = [p0[i] + v[i] * t + R * np.sin(theta2) * n1[i] + R * np.cos(theta) * n2[i] for i in [0, 1, 2]]
		# "Outer Cap"
		X2, Y2, Z2 = [p0[i] + rsample[i] * np.sin(theta) * n1[i] + rsample[i] * np.cos(theta) * n2[i] for i in [0, 1, 2]]
		# "Earth Center cap"
		X3, Y3, Z3 = [p0[i] + v[i] * mag + rsample[i] * np.sin(theta) * n1[i] + rsample[i] * np.cos(theta) * n2[i] for i in [0, 1, 2]]

		self.actors['umbra'] = self.ax.plot_surface(X, Y, Z, color=shadow_color, edgecolor=None)
		self.actors['umbra_cap1'] = self.ax.plot_surface(X2, Y2, Z2, color=shadow_color, edgecolor=shadow_edge)
		self.actors['umbra_cap2'] = self.ax.plot_surface(X3, Y3, Z3, color=shadow_color, edgecolor=None)

	def draw(self):
		"""Draw orbit visualisation representing current data sources.
		
		Will draw:
			Single orbit starting at index position
			Pos, identifed by x
			Sun and sun vector at 1.5 x the orbit radius
			Earth umbra
		"""
		self.plotOrbit()
		self.plotStart()
		self.plotEnd()

		self.ax.set_xlabel(self.opts['x_units'])
		self.ax.set_ylabel(self.opts['y_units'])
		self.ax.set_zlabel(self.opts['z_units'])
		
		if self.orbit_points is not None:
			self.plotPos(gizmo=False)
		
		if self.sun is not None:
			self.sun.transform(self.source.sun[self.index])
			self.sun.draw()
			self.drawUmbra()

	def _createOptHelp(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['color'] = "Colour to be used for orbit trajectory. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['color'])
				self.opts_help['pos_marker'] = "Marker to be used for indexed orbit position. dflt: '{opt}'. fmt: matplotlib marker string".format(opt=self._dflt_opts['pos_marker'])
				self.opts_help['marker_size'] = "Marker size to be used for indexed orbit position. dflt: '{opt}'. fmt: int".format(opt=self._dflt_opts['marker_size'])
				self.opts_help['umbra_color'] = "Color to be used with the umbra cylinder. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['umbra_color'])
				self.opts_help['umbra_edge'] = "Color to be used with the umbra edge. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['umbra_color'])
				self.opts_help['orbital_length'] = "Multiplier for how many orbital periods are to be plotted. dflt: '{opt}'. fmt: float".format(opt=self._dflt_opts['orbital_length'])
				self.opts_help['x_units'] = "Unit to be displayed on x axis. dflt: '{opt}'.".format(opt=self._dflt_opts['x_units'])
				self.opts_help['y_units'] = "Unit to be displayed on y axis. dflt: '{opt}'.".format(opt=self._dflt_opts['y_units'])
				self.opts_help['z_units'] = "Unit to be displayed on z axis. dflt: '{opt}'.".format(opt=self._dflt_opts['z_units'])
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.setDefaultOptions()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))

def plotVectors(ax, points, dirs, scale=1, **kwargs):
	# print(points[0])
	# print(points[1])
	# print(points[2])
	# print(dirs[0] - points[0])
	# print(dirs[1] - points[1])
	# print(dirs[2] - points[2])

	#TODO: Not working properly when vectors are rows

	# scale = 10*np.linalg.norm(dirs) / np.linalg.norm(points)

	if points.shape != dirs.shape:
		print("Same number of points and vectors must be supplied")
	if len(points.shape) == 2:
		m, n = points.shape
		if m > n:
			ax.quiver(points[0, :], points[1, :], points[2, :],
						dirs[0, :] * scale, dirs[1, :] * scale, dirs[2, :] * scale,  # noqa: E128
						**kwargs)  # noqa: E126
		else:
			ax.quiver(points[:, 0], points[:, 1], points[:, 2],
						dirs[:, 0] * scale, dirs[:, 1] * scale, dirs[:, 2] * scale,  # noqa: E128
						**kwargs)  # noqa: E126
	else:
		ax.quiver(points[0], points[1], points[2],
					dirs[0] * scale, dirs[1] * scale, dirs[2] * scale,  # noqa: E128
					**kwargs)  # noqa: E126




