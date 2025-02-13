
import numpy as np
import satplot.util.constants as c
import satplot.visualiser.colours as colours
from satplot.visualiser.assets.base import BaseAsset, SimpleAsset
from satplot.visualiser.controls import console


from vispy import scene
from vispy.visuals import transforms as vTransforms

class BodyGizmo(SimpleAsset):
	def __init__(self, name=None, v_parent=None, scale=1, width=1):
		super().__init__(name, v_parent)
						
		self._setDefaultOptions()
		self._initData()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self):
		if self.data['name'] is None:
			self.data['name'] = 'body_frame_gizmo'
		pass
		
	def setSource(self, *args, **kwargs):
		self.opts['gizmo_scale']['value'] = args[0]
		self.opts['gizmo_width']['value'] = args[1]
		pass

	def _createVisuals(self):
		self.visuals['gizmo'] = scene.visuals.XYZAxis(width=self.opts['gizmo_width']['value'],
														parent=None)
		scale_vec = self.opts['gizmo_scale']['value']*np.ones((1,3))
		self.visuals['gizmo'].transform = vTransforms.STTransform(scale=scale_vec).as_matrix()

	def setTransform(self, pos=(0,0,0), rotation=np.eye(3)):
		T = np.eye(4)
		T[0:3,0:3] = self.opts['gizmo_scale']['value']*rotation
		T[0:3,3] = np.asarray(pos).reshape(-1,3)
		self.visuals['gizmo'].transform = vTransforms.linear.MatrixTransform(T.T)

	def _setDefaultOptions(self):
		self._dflt_opts = {}

		self._dflt_opts['gizmo_X_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoXColour}
		self._dflt_opts['gizmo_Y_axis_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoYColour}
		self._dflt_opts['gizmo_Z_axis_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'callback': self.setGizmoZColour}
		self._dflt_opts['gizmo_width'] = {'value': 1,
										  		'type': 'number',
												'help': '',
												'callback': self.setGizmoWidth}
		self._dflt_opts['gizmo_scale'] = {'value': 1,
										  		'type': 'number',
												'help': '',
												'callback': self.setGizmoScale}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setGizmoXColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_X_axis_colour']['value'] = colour
	
	def setGizmoYColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_Y_axis_colour']['value'] = colour
	
	def setGizmoZColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_Z_axis_colour']['value'] = colour

	def setTemporaryGizmoXColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
	
	def setTemporaryGizmoYColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
	
	def setTemporaryGizmoZColour(self, colour):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)

	def restoreGizmoColours(self):
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']))
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']))
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']))
		self.visuals['gizmo'].set_data(color=old_colour_arr)

	def setGizmoWidth(self, value):
		self.opts['gizmo_width']['value'] = value
		self.visuals['gizmo'].set_data(width=value)

	def setGizmoScale(self, value):
		old_scale = self.opts['gizmo_scale']['value']
		old_transform_matrix = self.visuals['gizmo'].transform.matrix
		base_rotation = old_transform_matrix[0:3,0:3] / old_scale
		pos = old_transform_matrix[0:3,3]
		self.opts['gizmo_scale']['value'] = value
		self.setTransform(pos=pos, rotation=base_rotation)
		self.visuals['gizmo'].update()

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
		s = vTransforms.STTransform(translate=self.translate, scale=self.scale)
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