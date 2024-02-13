import numpy as np
import logging
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import satplot.model.geometry.primgeom as pg
import satplot.util.constants as consts

import satplot.model.geometry.transformations as transforms

logger = logging.getLogger(__name__)


class Gizmo(object):
	"""A Gizmo asset for satplot visualisers
	
	Consists of orthogonal x,y and z vectors

	Asset draw options can be edited by accessing object.opts[key]
	Options help can be viewed via object.opts_help
	Valid options are:
		'x_color': Colour to be used for x vector
		'y_color': Colour to be used for y vector
		'z_color': Colour to be used for z vector
		'line_weight': Weight of vectors
	"""
	def __init__(self, parent, ax, scale):
		"""Creates asset instance
		
		Parameters
		----------
		parent : {object}
			Object calling the sun instance
		ax : {Axes3DSubplot}
			Axes the asset is to be drawn on
		scale : {float}
			Scale of the vectors
		"""
		self.set_dflt_options()
		self.T = np.eye(4)
		self.T[:, 3] = np.ones(4)
		self.ax = ax
		self.actors = {}
		self.init_basepoints = np.array([[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]])
		self.init_points = np.array([[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1]])
		self.init_points[0:3, 0:3] = self.opts['length'] * np.eye(3)
		self.points = self.init_points.copy()
		self.basepoints = self.init_basepoints.copy()
		self.scale = np.eye(4)
		self.scale[0:3, 0:3] = scale * np.eye(3)

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Gizmo
			Reference to the asset to be used in actor lists.
		"""
		self.remove()
		self._apply_opts()
		x_ray = np.vstack((self.basepoints[0, 0:3], self.points[0, 0:3]))
		y_ray = np.vstack((self.basepoints[1, 0:3], self.points[1, 0:3]))
		z_ray = np.vstack((self.basepoints[2, 0:3], self.points[2, 0:3]))
		self.actors['gizmo_x'] = self.ax.plot(x_ray[:, 0], x_ray[:, 1], x_ray[:, 2], color=self.opts['x_color'], linewidth=self.opts['line_weight'])
		self.actors['gizmo_y'] = self.ax.plot(y_ray[:, 0], y_ray[:, 1], y_ray[:, 2], color=self.opts['y_color'], linewidth=self.opts['line_weight'])
		self.actors['gizmo_z'] = self.ax.plot(z_ray[:, 0], z_ray[:, 1], z_ray[:, 2], color=self.opts['z_color'], linewidth=self.opts['line_weight'])
		# self.actors['gizmo_cent'] = self.ax.plot([z_ray[0, 0], z_ray[0, 0]], [z_ray[0, 1], z_ray[0, 1]], [z_ray[0, 2], z_ray[0, 2]], color='k', marker='o', markersize=5)
		return self

	def remove(self):
		"""Remove gizmo asset from the axes
		
		Removes all gizmo asset actors which are present on the axes
		"""
		if 'gizmo_x' in self.actors.keys():
			logger.debug("Removing gizmo from orbit plot")
			self.actors['gizmo_x'][0].remove()
			self.actors['gizmo_y'][0].remove()
			self.actors['gizmo_z'][0].remove()
			del self.actors['gizmo_x']
			del self.actors['gizmo_y']
			del self.actors['gizmo_z']

	def transform(self, rot, trans):
		"""Move and rotate the asset to the desired position
		
		Parameters
		----------
		rot : {(3,3) ndarray}
			Rotation matrix rotating the gizmo from the canonical ijk vectors
		trans : {(3,) ndarray}
			Base point of the gizmo in the axes frame
		"""
		self.T[0:3, 0:3] = rot
		self.T[0:3, 3] = trans
		# print(self.T)
		self.points = np.dot(self.T, np.dot(self.scale, self.init_points.T)).T
		self.basepoints = np.dot(self.T, self.init_basepoints.T).T

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		self._dflt_opts = {}
		
		self._dflt_opts['x_color'] = np.asarray([1, 0, 0])
		self._dflt_opts['y_color'] = np.asarray([0, 1, 0])
		self._dflt_opts['z_color'] = np.asarray([0, 0, 1])
		self._dflt_opts['line_weight'] = 2
		self._dflt_opts['length'] = 1

		self.opts = self._dflt_opts.copy()
		self._create_opt_help()

	def _apply_opts(self):		
		pass

	def _create_opt_help(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['x_color'] = "Colour to be used for x_axis of gizmo. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['x_color'])
				self.opts_help['y_color'] = "Colour to be used for y_axis of gizmo. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['y_color'])
				self.opts_help['z_color'] = "Colour to be used for x_axis of gizmo. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['z_color'])
				self.opts_help['line_weight'] = "Weight of gizmo lines. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['line_weight'])
				self.opts_help['length'] = "Length of gizmo lines. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['length'])
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.set_dflt_options()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))


class Sun(object):
	"""A Sun asset for satplot visualisers
	
	Consists of a disc and normal vector signifying incoming solar radiation.

	Asset draw options can be edited by accessing object.opts[key]
	Options help can be viewed via object.opts_help
	Valid options are:
		'color': Colour to be used for sun marker
		'vec_length': Length of sun vector displayed, as multiple of sun position length
		'radius': Sun spot subtending angle (deg)
	"""

	def __init__(self, parent, ax, scale):
		"""Creates asset instance
		
		Parameters
		----------
		parent : {object}
			Object calling the sun instance
		ax : {Axes3DSubplot}
			Axes the asset is to be drawn on
		scale : {float}
			Scale of the sun vector as a multiple of the pos vector length of the asset
		"""
		self.set_dflt_options()
		self.T = np.eye(4)
		# self.T[:, 3] = np.ones(4)
		self.ax = ax
		self.sun_dist = scale

		self.actors = {}
		# The following are recalculated when new options are applied
		# Initial sun pos that sun is rotated from
		self.init_pos = np.array((0, 0, 0, 1))
		self.pos = self.init_pos.copy()

		# Initial point along sun vector at which arrow ends
		self.arrow_length = self.opts['vec_length'] * self.sun_dist
		self.init_arrow_end = np.array((-self.arrow_length, 0, 0, 1))
		self.arrow_end = self.init_arrow_end.copy()

		# Sun disc
		self._theta = np.arange(0, 2 * np.pi, 0.1)  
		self.sun_radius = 2 * np.deg2rad(self.opts['radius']) * self.sun_dist
		self.init_xyz = np.array([np.zeros(self._theta.size), self.sun_radius * np.sin(self._theta), self.sun_radius * np.cos(self._theta), np.ones(self._theta.size)]).T
		self.xyz = self.init_xyz.copy()

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Sun
			Reference to the asset to be used in actor lists.
		"""
		self.remove()
		self._apply_opts()
		# draw circle patch
		new_verts_list = [list(map(tuple, self.xyz[:, 0:3]))] 
		p = Poly3DCollection(new_verts_list) 
		p.set_color(self.opts['color'])
		# self.ax.add_collection3d(p)

		sal = np.vstack((self.pos, self.arrow_end))
		# sun_arrow = self.ax.plot(sal[:, 0], sal[:, 1], sal[:, 2], color=0.8 * self.opts['color'])
		sun_arrow = self.ax.plot(sal[:, 0], sal[:, 1], sal[:, 2], color=self.opts['color'])
		sun_outline = self.ax.plot(self.xyz[:, 0], self.xyz[:, 1], self.xyz[:, 2], color=self.opts['color'], linewidth=2)
		# logger.debug("Adding sun to orbit plot at %f, %f, %f", self.sun[0], self.sun[0], self.sun[0])

		# self.actors['sun'] = p
		self.actors['sun_arrow'] = sun_arrow
		self.actors['sun_outline'] = sun_outline

		return self

	def remove(self):
		"""Remove sun asset from the axes
		
		Removes all sun asset actors which are present on the axes
		"""
		if 'sun' in self.actors.keys():
			self.actors['sun'].remove()
			del self.actors['sun']
		if 'sun_arrow' in self.actors.keys():
			self.actors['sun_arrow'][0].remove()
			del self.actors['sun_arrow']
		if 'sun_outline' in self.actors.keys():
			self.actors['sun_outline'][0].remove()			
			del self.actors['sun_outline']

	def transform(self, sun_pos):
		"""Move and rotate the asset to the desired position
		
		The solar rad vector will always point to the origin of the frame.
		
		Parameters
		----------
		sun_pos : {(3,) ndarray}
			Position of the sun asset
		"""
		# TODO: something wrong with this, is producing a scale effect.
		# self.sun[0:3] = self.sun_dist * pg.unitVector(sun_pos)

		

		# Fill homogenous transformation matrix
		# Translation
		self.T[0:3, 3] = self.sun_dist * pg.unitVector(sun_pos)
		# Rotation
		rot = transforms.rotationMatrix(np.array((1, 0, 0)), pg.unitVector(sun_pos))

		self.T[0:3, 0:3] = rot

		# sun_vec = -pg.unitVector(sun_pos)
		# avec = np.array((1, 0, 0))
		# if np.all(np.isclose(abs(sun_vec), avec)):
		# 	avec = np.array((0, 1, 0))
		# avec2 = np.cross(sun_vec, avec)
		# avec3 = np.cross(sun_vec, avec2)

		# rot = np.array([[avec2[0], avec3[0], sun_vec[0]], [avec2[1], avec3[1], sun_vec[1]], [avec2[2], avec3[2], sun_vec[2]]])

		self.pos = np.dot(self.T, self.init_pos.T).T
		self.arrow_end = np.dot(self.T, self.init_arrow_end.T).T
		self.xyz = np.dot(self.T, self.init_xyz.T).T

		# self.pos = np.dot(self.init_pos.T, self.T).T
		# self.arrow_end = np.dot(self.init_arrow_end.T, self.T).T
		# self.xyz = np.dot(self.init_xyz.T, self.T).T

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		self._dflt_opts = {}
		
		self._dflt_opts['color'] = np.asarray([255, 157, 0]) / 256
		# self._dflt_opts['sun_arrow_head_size'] = 10
		self._dflt_opts['vec_length'] = 0.1
		self._dflt_opts['radius'] = 2

		self.opts = self._dflt_opts.copy()
		self._create_opt_help()

	def _apply_opts(self):		
		self.sun_radius = 2 * np.deg2rad(self.opts['radius']) * self.sun_dist
		self.init_xyz = np.array([np.zeros(self._theta.size), self.sun_radius * np.sin(self._theta), self.sun_radius * np.cos(self._theta), np.ones(self._theta.size)]).T
		self.arrow_length = self.opts['vec_length'] * self.sun_dist
		self.init_arrow_end = np.array((-self.arrow_length, 0, 0, 1))
		self.arrow_end = np.dot(self.T, self.init_arrow_end.T).T
		self.xyz = np.dot(self.T, self.init_xyz.T).T

		self.init_pos = np.array((0, 0, 0, 1))
		self.pos = np.dot(self.T, self.init_pos).T

		self._theta = np.arange(0, 2 * np.pi, 0.1)  
		self.sun_radius = 2 * np.deg2rad(self.opts['radius']) * self.sun_dist

	def _create_opt_help(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['color'] = "Colour to be used for sun marker. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['color'])
				# self.opts_help['sun_arrow_head_size'] = "Arrow head scale to be used for sun indicator. dflt: '{opt}'. fmt: int".format(opt=self._dflt_opts['sun_arrow_head_size'])
				self.opts_help['vec_length'] = "Length of sun vector displayed, as multiple of sun position length. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['vec_length'])
				self.opts_help['radius'] = "Sun spot subtending angle. dflt: '{opt}'. fmt: float >0".format(opt=self._dflt_opts['radius'])
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.set_dflt_options()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))


class Earth(object):
	"""An Earth asset for satplot visualisers
	
	Consists of an earth wireframe, equator and earth axis

	Asset draw options can be edited by accessing object.opts[key]
	Options help can be viewed via object.opts_help
	Valid options are:
		'color': Colour to be used for sun marker
		'vec_length': Length of sun vector displayed, as multiple of sun position length
		'radius': Sun spot subtending angle (deg)
	"""

	def __init__(self, parent, ax):
		"""Creates asset instance
		
		Parameters
		----------
		parent : {object}
			Object calling the earth instance
		ax : {Axes3DSubplot}
			Axes the asset is to be drawn on
		"""
		self.set_dflt_options()
		self.ax = ax
		self.actors = {}

		u, v = np.mgrid[0:2 * np.pi:25j, 0:np.pi:13j]
		self.x = consts.R_EARTH * np.cos(u) * np.sin(v)
		self.y = consts.R_EARTH * np.sin(u) * np.sin(v)
		self.z = consts.R_EARTH * np.cos(v)
		
		theta = np.arange(0, 2 * np.pi, 0.1)
		self.x1 = consts.R_EARTH * np.cos(theta)
		self.y1 = consts.R_EARTH * np.sin(theta)
		self.z1 = np.zeros(self.x1.size)

		# TODO: add earth texture onto sphere

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Earth
			Reference to the asset to be used in actor lists.
		"""
		self.remove()
		self._apply_opts()
		self.actors['wf'] = self.ax.plot_wireframe(self.x, self.y, self.z, color=self.opts['wf_color'], linewidth=self.opts['wf_weight'])
		self.actors['eq'] = self.ax.plot(self.x1, self.y1, self.z1, color=self.opts['eq_color'], linewidth=self.opts['eq_weight'])
		self.actors['axis'] = self.ax.plot([0, 0], [0, 0], [-1.1 * consts.R_EARTH, 1.1 * consts.R_EARTH], color=self.opts['axis_color'], linewidth=self.opts['axis_weight'])

	def remove(self):
		"""Remove earth asset from the axes
		
		Removes all earth asset actors which are present on the axes
		"""
		if 'wf' in self.actors.keys():
			self.actors['wf'].remove()
			self.actors['eq'][0].remove()
			self.actors['axis'][0].remove()
			del self.actors['wf']
			del self.actors['eq']
			del self.actors['axis']

	def transform(self, sun_pos):
		"""NOT YET IMPLEMENTED
		Move and rotate the asset to the desired position
		
		The solar rad vector will always point to the origin of the frame.
		
		Parameters
		----------
		sun_pos : {(3,) ndarray}
			Position of the sun asset
		"""
		pass

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		self._dflt_opts = {}
		
		self._dflt_opts['wf_color'] = np.asarray([0, 0, 0])
		self._dflt_opts['wf_weight'] = 0.5
		self._dflt_opts['axis_color'] = np.asarray([1, 0, 0])
		self._dflt_opts['axis_weight'] = 1
		self._dflt_opts['eq_color'] = np.asarray([1, 0, 0])
		self._dflt_opts['eq_weight'] = 1

		self.opts = self._dflt_opts.copy()
		self._create_opt_help()

	def _apply_opts(self):		
		pass

	def _create_opt_help(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['wf_color'] = "Colour to be used for wireframe. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['wf_color'])
				self.opts_help['axis_color'] = "Colour to be used for earth axis. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['axis_color'])
				self.opts_help['eq_color'] = "Colour to be used for earth equator. dflt: '{opt}'. fmt: matplotlib color string or (4,) np array".format(opt=self._dflt_opts['eq_color'])
				self.opts_help['wf_weight'] = "Weight of wireframe. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['wf_weight'])
				self.opts_help['axis_weight'] = "Weight of earth axis. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['axis_weight'])
				self.opts_help['eq_weight'] = "Weight of earth equator. dflt: '{opt}'. fmt: float [0,inf)".format(opt=self._dflt_opts['eq_weight'])				
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.set_dflt_options()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))


class Cursor2D(object):
	def __init__(self, parent, ax, val, vert=True):
		self.vert = vert
		self.val = val
		self.parent = parent
		self.ax = ax

		if self.vert:
			extents = self.ax.get_ylim()
			self.x = [val, val]
			self.y = [extents[0], extents[1]]
		else:
			extents = self.ax.get_xlim()
			self.x = [extents[0], extents[1]]
			self.y = [val, val]

		self.actors = {}

	def draw(self, val):
		self.remove()
		self._apply_opts()
		self._update_pos(val)
		self.actors['cursor'] = self.ax.plot(self.x, self.y, color='k', linewidth=0.5)

		return self

	def _update_pos(self, index):
		val = self.parent.source.timespan.seconds_since_start()[index]
		if self.vert:
			extents = self.ax.get_ylim()

			self.x = [val, val]
			if not self.parent.drawn:
				self.y = [extents[0], extents[1]]
		else:
			extents = self.ax.get_xlim()
			if not self.parent.drawn:
				self.x = [extents[0], extents[1]]
			self.y = [val, val]		

	def remove(self):
		if 'cursor' in self.actors.keys():
			self.actors['cursor'][0].remove()
			del self.actors['cursor']

	def transform(self):
		pass

	def set_dflt_options(self):
		pass

	def _create_opt_help(self):
		pass

	def _apply_opts(self):
		pass
