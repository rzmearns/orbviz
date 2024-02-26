
import numpy as np
import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset
from satplot.visualiser.controls import console

from vispy import scene
from vispy.visuals.transforms import STTransform

# from .line import LineVisual

# XYZAxis = create_visual_node(XYZAxisVisual)

# class XYZAxisVisual(LineVisual):
#     """
#     Simple 3D axis for indicating coordinate system orientation. Axes are
#     x=red, y=green, z=blue.
#     """

#     def __init__(self, **kwargs):
#         pos = np.array([[0, 0, 0],
#                         [1, 0, 0],
#                         [0, 0, 0],
#                         [0, 1, 0],
#                         [0, 0, 0],
#                         [0, 0, 1]])
#         color = np.array([[1, 0, 0, 1],
#                           [1, 0, 0, 1],
#                           [0, 1, 0, 1],
#                           [0, 1, 0, 1],
#                           [0, 0, 1, 1],
#                           [0, 0, 1, 1]])
#         connect = 'segments'
#         method = 'gl'

#         kwargs.setdefault('pos', pos)
#         kwargs.setdefault('color', color)
#         kwargs.setdefault('connect', connect)
#         kwargs.setdefault('method', method)

#         LineVisual.__init__(self, **kwargs)

class ViewBoxGizmo(BaseAsset):
	def __init__(self, canvas=None, parent=None, translate=(0,0), scale=(1,1,1,1)):
		self.parent = parent
		self.canvas = canvas
		
		self.visuals = {}
		self.scale = scale
		self.translate = translate
		self.requires_recompute = False
		self._setDefaultOptions()	
		self.draw()

		self.visuals['gizmo'] = scene.visuals.XYZAxis(parent=self.parent)
		s = STTransform(translate=self.translate, scale=self.scale)
		affine = s.as_matrix()
		self.visuals['gizmo'].transform = affine

	def compute(self):
		pass

	def draw(self):
		pass

	def recompute(self):
		pass

	def attachCamera(self, cam):
		self.cam = cam

	def onMouseMove(self, event):
		# console.send("Gizmo received event")
		if event.button == 1 and event.is_dragging:
			# console.send("Gizmo updating")
			self.visuals['gizmo'].transform.reset()

			self.visuals['gizmo'].transform.rotate(self.cam.roll, (0, 0, 1))
			self.visuals['gizmo'].transform.rotate(self.cam.elevation, (1, 0, 0))
			self.visuals['gizmo'].transform.rotate(self.cam.azimuth, (0, 1, 0))

			self.visuals['gizmo'].transform.scale((self.scale[0], self.scale[1], 0.001))
			self.visuals['gizmo'].transform.translate((self.translate[0], self.translate[1]))
			self.visuals['gizmo'].update()	

	def _setDefaultOptions(self):
		self._dflt_opts = {}

		self._dflt_opts['plot_gizmo'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'callback': self.setGizmoAssetVisibility}
		self._dflt_opts['gizmo_X_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoXColour}
		self._dflt_opts['gizmo_Y_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoYColour}
		self._dflt_opts['gizmo_Z_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoZColour}

		# sun radius calculated using 6deg angular size

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self):
		pass

	def setGizmoAssetVisibility(self, state):
		raise NotImplementedError
	
	def setGizmoXColour(self, colour):
		raise NotImplementedError
	
	def setGizmoYColour(self, colour):
		raise NotImplementedError
	
	def setGizmoZColour(self, colour):
		raise NotImplementedError