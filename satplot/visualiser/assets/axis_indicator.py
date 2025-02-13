import numpy as np

from vispy.scene import visuals as scenevisuals
from vispy import visuals

class XYZAxisVisual(visuals.LineVisual):
	"""
	Simple 3D axis for indicating coordinate system orientation. Axes are
	x=red, y=green, z=blue.
	"""

	def __init__(self, center=(0,0,0), scale=1, **kwargs):
		pos = scale*np.array([[0, 0, 0],
						[1, 0, 0],
						[0, 0, 0],
						[0, 1, 0],
						[0, 0, 0],
						[0, 0, 1]])
		pos = np.asarray(center) + pos
		color = np.array([[1, 0, 0, 1],
						  [1, 0, 0, 1],
						  [0, 1, 0, 1],
						  [0, 1, 0, 1],
						  [0, 0, 1, 1],
						  [0, 0, 1, 1]])
		connect = 'segments'
		method = 'gl'
		kwargs.setdefault('pos', pos)
		kwargs.setdefault('color', color)
		kwargs.setdefault('connect', connect)
		kwargs.setdefault('method', method)

		visuals.LineVisual.__init__(self, **kwargs)

XYZAxis = scenevisuals.create_visual_node(XYZAxisVisual)