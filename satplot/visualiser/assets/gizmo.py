import numpy as np
import numpy.typing as nptyping
import vispy.scene as scene

from PyQt5 import QtGui

from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.transforms as vTransforms

import satplot.util.constants as c
import satplot.visualiser.colours as colours
import satplot.visualiser.assets.base_assets as base_assets



class BodyGizmo(base_assets.AbstractSimpleAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None, scale:int=1, width:int=1):
		super().__init__(name, v_parent)
						
		self._setDefaultOptions()
		self._initData()
		self._createVisuals()

		self._attachToParentView()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'body_frame_gizmo'
		pass
		
	def setSource(self, *args, **kwargs) -> None:
		pass

	def _createVisuals(self) -> None:
		self.visuals['gizmo'] = scene.visuals.XYZAxis(width=self.opts['gizmo_width']['value'],
														parent=None)
		scale_vec = self.opts['gizmo_scale']['value']*np.ones((1,3))
		self.visuals['gizmo'].transform = vTransforms.STTransform(scale=scale_vec).as_matrix()


	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray=np.eye(3)) -> None:
		if self.isStale():
			T = np.eye(4)
			T[0:3,0:3] = self.opts['gizmo_scale']['value']*rotation
			T[0:3,3] = np.asarray(pos).reshape(-1,3)
			print(f'setTransform:{pos=}')
			self.visuals['gizmo'].transform = vTransforms.linear.MatrixTransform(T.T)
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['gizmo_X_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoXColour,
											'widget': None}
		self._dflt_opts['gizmo_Y_axis_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoYColour,
											'widget': None}
		self._dflt_opts['gizmo_Z_axis_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoZColour,
											'widget': None}
		self._dflt_opts['gizmo_width'] = {'value': 3,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoWidth,
											'widget': None}
		self._dflt_opts['gizmo_scale'] = {'value': 700,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoScale,
											'widget': None}

		self.opts = self._dflt_opts.copy()

	#----- OPTIONS CALLBACKS -----#
	def setGizmoXColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_X_axis_colour']['value'] = colour
	
	def setGizmoYColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_Y_axis_colour']['value'] = colour
	
	def setGizmoZColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
		self.opts['gizmo_Z_axis_colour']['value'] = colour

	def setTemporaryGizmoXColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
	
	def setTemporaryGizmoYColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)
	
	def setTemporaryGizmoZColour(self, colour:tuple[float,float,float]) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(colour))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(colour))
		self.visuals['gizmo'].set_data(color=old_colour_arr)

	def restoreGizmoColours(self) -> None:
		old_colour_arr = self.visuals['gizmo'].color
		old_colour_arr[0,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']))
		old_colour_arr[1,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']))
		old_colour_arr[2,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']))
		old_colour_arr[3,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']))
		old_colour_arr[4,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']))
		old_colour_arr[5,0:3] = np.asarray(colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']))
		self.visuals['gizmo'].set_data(color=old_colour_arr)

	def setGizmoWidth(self, value:int) -> None:
		self.opts['gizmo_width']['value'] = value
		self.visuals['gizmo'].set_data(width=value)

	def setGizmoScale(self, value:float) -> None:
		old_scale = self.opts['gizmo_scale']['value']
		old_transform_matrix = self.visuals['gizmo'].transform.matrix
		unscaled_rotation = old_transform_matrix[0:3,0:3] / old_scale
		pos = old_transform_matrix[3,0:3]
		self.opts['gizmo_scale']['value'] = value
		self._setStaleFlag()
		self.setTransform(pos=pos, rotation=unscaled_rotation)

class ViewBoxGizmo(base_assets.AbstractAsset):
	def __init__(self, canvas:scene.canvas.SceneCanvas|None=None,
						 parent:ViewBox|None=None,
						 translate:tuple[float,float]=(0,0),
						 scale:tuple[float,float,float,float]=(1,1,1,1)):
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

	def compute(self) -> None:
		pass

	def draw(self) -> None:
		pass

	def recompute(self) -> None:
		pass

	def attachCamera(self, cam) -> None:
		self.cam = cam

	def onMouseMove(self, event:QtGui.QMouseEvent) -> None:
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

	def _setDefaultOptions(self) -> None:
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

	def _createOptHelp(self) -> None:
		pass

	def setGizmoAssetVisibility(self, state:bool) -> None:
		raise NotImplementedError
	
	def setGizmoXColour(self, colour:tuple[float,float,float]) -> None:
		raise NotImplementedError
	
	def setGizmoYColour(self, colour:tuple[float,float,float]) -> None:
		raise NotImplementedError
	
	def setGizmoZColour(self, colour:tuple[float,float,float]) -> None:
		raise NotImplementedError