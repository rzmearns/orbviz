import numpy as np
import logging

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
		raise NotImplementedError()

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Gizmo
			Reference to the asset to be used in actor lists.
		"""
		raise NotImplementedError()		

	def remove(self):
		"""Remove gizmo asset from the axes
		
		Removes all gizmo asset actors which are present on the axes
		"""
		raise NotImplementedError()

	def transform(self, rot, trans):
		"""Move and rotate the asset to the desired position
		
		Parameters
		----------
		rot : {(3,3) ndarray}
			Rotation matrix rotating the gizmo from the canonical ijk vectors
		trans : {(3,) ndarray}
			Base point of the gizmo in the axes frame
		"""
		raise NotImplementedError()		

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		raise NotImplementedError()

	def _apply_opts(self):		
		raise NotImplementedError()

	def _create_opt_help(self):
		raise NotImplementedError()

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
		raise NotImplementedError()

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Sun
			Reference to the asset to be used in actor lists.
		"""
		raise NotImplementedError()

	def remove(self):
		"""Remove sun asset from the axes
		
		Removes all sun asset actors which are present on the axes
		"""
		raise NotImplementedError()

	def transform(self, sun_pos):
		"""Move and rotate the asset to the desired position
		
		The solar rad vector will always point to the origin of the frame.
		
		Parameters
		----------
		sun_pos : {(3,) ndarray}
			Position of the sun asset
		"""
		raise NotImplementedError()

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		raise NotImplementedError()

	def _apply_opts(self):		
		raise NotImplementedError()

	def _create_opt_help(self):
		raise NotImplementedError()

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
		"""
		raise NotImplementedError()

	def draw(self):
		"""(Re)Draw the asset
		
		Returns
		-------
		Earth
			Reference to the asset to be used in actor lists.
		"""
		raise NotImplementedError()

	def remove(self):
		"""Remove earth asset from the axes
		
		Removes all earth asset actors which are present on the axes
		"""
		raise NotImplementedError()

	def transform(self, sun_pos):
		"""NOT YET IMPLEMENTED
		Move and rotate the asset to the desired position
		
		The solar rad vector will always point to the origin of the frame.
		
		Parameters
		----------
		sun_pos : {(3,) ndarray}
			Position of the sun asset
		"""
		raise NotImplementedError()

	def set_dflt_options(self):
		""" Sets the default options for the orbit_visualiser		
		"""
		raise NotImplementedError()

	def _apply_opts(self):		
		raise NotImplementedError()

	def _create_opt_help(self):
		raise NotImplementedError()

class Cursor2D(object):
	def __init__(self, parent, ax, val, vert=True):
		raise NotImplementedError()

	def draw(self, val):
		raise NotImplementedError()

	def _update_pos(self, index):
		raise NotImplementedError()	

	def remove(self):
		raise NotImplementedError()

	def transform(self):
		raise NotImplementedError()

	def set_dflt_options(self):
		raise NotImplementedError()

	def _create_opt_help(self):
		raise NotImplementedError()

	def _apply_opts(self):
		raise NotImplementedError()
