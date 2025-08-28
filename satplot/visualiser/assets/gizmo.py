

import numpy as np
import numpy.typing as nptyping

from PyQt5 import QtGui

import vispy.scene as scene
from vispy.scene.widgets.viewbox import ViewBox
import vispy.visuals.transforms as vTransforms

import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.colours as colours


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
			self.visuals['gizmo'].transform = vTransforms.linear.MatrixTransform(T.T)
			self._clearStaleFlag()

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['gizmo_X_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoXColour,
											'widget_data': None}
		self._dflt_opts['gizmo_Y_axis_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoYColour,
											'widget_data': None}
		self._dflt_opts['gizmo_Z_axis_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoZColour,
											'widget_data': None}
		self._dflt_opts['gizmo_width'] = {'value': 3,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoWidth,
											'widget_data': None}
		self._dflt_opts['gizmo_scale'] = {'value': 700,
										  		'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoScale,
											'widget_data': None}

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

class ViewBoxGizmo(base_assets.AbstractSimpleAsset):
	def __init__(self, name:str|None=None, v_parent:ViewBox|None=None,
						viewbox_location:tuple[float,float]=(0,0)):
		super().__init__(name, v_parent)

		self._setDefaultOptions()
		self._initData()
		self.location = [0,0]
		self._createVisuals()
		self._attachToParentView()
		self.setViewBoxTransform()

	def _initData(self) -> None:
		if self.data['name'] is None:
			self.data['name'] = 'viewbox_eci_gizmo'

	def setSource(self, *args, **kwargs) -> None:
		pass

	def _createVisuals(self) -> None:

		self.visuals['origin'] = scene.visuals.Markers(pos=np.array([[0,0,0]]).reshape(1,3),
								  		edge_width=0,
										face_color=colours.normaliseColour(self.opts['origin_colour']['value']),
										edge_color=colours.normaliseColour(self.opts['origin_colour']['value']),
										size=self.opts['origin_scale']['value'],
										symbol='o')
		t_origin = vTransforms.STTransform(translate=self.location,
											scale=(self.opts['origin_scale']['value'],
													self.opts['origin_scale']['value'],
													self.opts['origin_scale']['value'], 1))
		self.visuals['origin'].transform = t_origin.as_matrix()


		self.visuals['gizmo'] = scene.visuals.XYZAxis(parent=None, width=self.opts['gizmo_width']['value'])
		self._updateAxesLengths()
		t_gizmo = vTransforms.STTransform(translate=self.location,
											scale=(self.opts['gizmo_scale']['value'],
													self.opts['gizmo_scale']['value'],
													self.opts['gizmo_scale']['value'], 1))
		self.visuals['gizmo'].transform = t_gizmo.as_matrix()


		self.setViewBoxTransform()

	def setTransform(self, pos:tuple[float,float,float]|nptyping.NDArray=(0,0,0),
							 rotation:nptyping.NDArray=np.eye(3)) -> None:
		pass

	def onMouseMove(self, event:QtGui.QMouseEvent) -> None:
		if event.button == 1 and event.is_dragging:
			self.setViewBoxTransform()

	def onResize(self, event:QtGui.QResizeEvent) -> None:
		self.setViewBoxTransform()

	def deSerialise(self, state):
		super().deSerialise(state)
		self.setViewBoxTransform()

	def setViewBoxTransform(self) -> None:
		self.visuals['gizmo'].transform.reset()
		self.visuals['origin'].transform.reset()
		self._setRotationFromCamera()
		self._setViewBoxPosition()
		self.visuals['gizmo'].update()
		self.visuals['origin'].update()

	def _setViewBoxPosition(self) -> None:
		if 'top' in self.opts['gizmo_location']['value']:
			self.location[1] = 0 + 75
		elif 'bottom' in self.opts['gizmo_location']['value']:
			self.location[1] = self.data['v_parent'].canvas.native.height() - 75

		if 'left' in self.opts['gizmo_location']['value']:
			self.location[0] = 0 + 75
		elif 'right' in self.opts['gizmo_location']['value']:
			self.location[0] = self.data['v_parent'].canvas.native.width() - 75

		self.visuals['gizmo'].transform.scale((self.opts['gizmo_scale']['value'], self.opts['gizmo_scale']['value'], 0.001))
		self.visuals['gizmo'].transform.translate((self.location[0], self.location[1]))
		self.visuals['origin'].transform.scale((self.opts['origin_scale']['value'], self.opts['origin_scale']['value'], 0.001))
		self.visuals['origin'].transform.translate((self.location[0], self.location[1]))

	def _updateAxesLengths(self) -> None:
		origin_radius = (self.opts['origin_scale']['value']/2)/self.opts['gizmo_scale']['value']
		axes_pos = np.array([[origin_radius, 0, 0],
					[1, 0, 0],
					[0, origin_radius, 0],
					[0, 1, 0],
					[0, 0, origin_radius],
					[0, 0, 1]])
		self.visuals['gizmo'].set_data(pos=axes_pos)

	def _setRotationFromCamera(self) -> None:
		self.visuals['gizmo'].transform.rotate(90, (1, 0, 0))
		self.visuals['gizmo'].transform.rotate(self.data['v_parent'].camera.roll, (0, 0, 1))
		self.visuals['gizmo'].transform.rotate(self.data['v_parent'].camera.azimuth, (0, 1, 0))
		self.visuals['gizmo'].transform.rotate(self.data['v_parent'].camera.elevation, (1, 0, 0))

	def _setDefaultOptions(self) -> None:
		self._dflt_opts = {}

		self._dflt_opts['plot_gizmo'] = {'value': True,
												'type': 'boolean',
												'help': '',
												'static': True,
												'callback': self.setGizmoAssetVisibility,
												'widget_data': None}
		self._dflt_opts['gizmo_location'] = {'value': 'bottom_left',
												'type': 'option',
												'options': ['top_left','top_right','bottom_left','bottom_right'],
												'help': '',
												'static': True,
												'callback': self.setGizmoLocation,
												'widget_data': None}
		self._dflt_opts['gizmo_width'] = {'value': 2,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoWidth,
												'widget_data': None}
		self._dflt_opts['origin_scale'] = {'value': 12,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setOriginScale,
												'widget_data': None}
		self._dflt_opts['origin_colour'] = {'value': (0,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setOriginColour,
												'widget_data': None}
		self._dflt_opts['gizmo_scale'] = {'value': 30,
												'type': 'number',
												'help': '',
												'static': True,
												'callback': self.setGizmoScale,
												'widget_data': None}
		self._dflt_opts['gizmo_X_axis_colour'] = {'value': (255,0,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoXColour,
												'widget_data': None}
		self._dflt_opts['gizmo_Y_axis_colour'] = {'value': (0,255,0),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoYColour,
												'widget_data': None}
		self._dflt_opts['gizmo_Z_axis_colour'] = {'value': (0,0,255),
												'type': 'colour',
												'help': '',
												'static': True,
												'callback': self.setGizmoZColour,
												'widget_data': None}

		self.opts = self._dflt_opts.copy()
		self._createOptHelp()

	def _createOptHelp(self) -> None:
		pass

	def setGizmoAssetVisibility(self, state:bool) -> None:
		self.opts['plot_gizmo']['value'] = state
		if self.opts['plot_gizmo']['value']:
			self._attachToParentView()
		else:
			self._detachFromParentView()

	def setGizmoWidth(self, width:int) -> None:
		self.visuals['gizmo'].set_data(width=width)
		self.opts['gizmo_width']['value'] = width
		self.setViewBoxTransform()
	
	def setGizmoScale(self, scale:int) -> None:
		self.opts['gizmo_scale']['value'] = scale
		self._updateAxesLengths()
		self.setViewBoxTransform()

	def setGizmoLocation(self, opt_idx:int) -> None:
		self.opts['gizmo_location']['value'] = self.opts['gizmo_location']['options'][opt_idx]
		self.setViewBoxTransform()

	def setGizmoXColour(self, colour:tuple[float,float,float]) -> None:
		axes_colour = np.array([[*colours.normaliseColour(colour),1],
							[*colours.normaliseColour(colour),1],
							[*colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']),1]])
		self.visuals['gizmo'].set_data(color=axes_colour)
		self.setViewBoxTransform()
		self.opts['gizmo_X_axis_colour']['value'] = colour
	
	def setGizmoYColour(self, colour:tuple[float,float,float]) -> None:
		axes_colour = np.array([[*colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']),1],
							[*colours.normaliseColour(colour),1],
							[*colours.normaliseColour(colour),1],
							[*colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Z_axis_colour']['value']),1]])
		self.visuals['gizmo'].set_data(color=axes_colour)
		self.setViewBoxTransform()
		self.opts['gizmo_Y_axis_colour']['value'] = colour
	
	def setGizmoZColour(self, colour:tuple[float,float,float]) -> None:
		axes_colour = np.array([[*colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_X_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']),1],
							[*colours.normaliseColour(self.opts['gizmo_Y_axis_colour']['value']),1],
							[*colours.normaliseColour(colour),1],
							[*colours.normaliseColour(colour),1]])
		self.visuals['gizmo'].set_data(color=axes_colour)
		self.setViewBoxTransform()
		self.opts['gizmo_Z_axis_colour']['value'] = colour

	def setOriginScale(self, scale:int) -> None:
		self.opts['origin_scale']['value'] = scale
		self._updateOriginMarker()
		self._updateAxesLengths()
		self.setViewBoxTransform()

	def _updateOriginMarker(self) -> None:
		self.visuals['origin'].set_data(pos=np.array((0,0,0)).reshape(1,3),
										size=self.opts['origin_scale']['value'],
										face_color=colours.normaliseColour(self.opts['origin_colour']['value']),
										edge_color=colours.normaliseColour(self.opts['origin_colour']['value']))

	def setOriginColour(self, colour:tuple[float,float,float]) -> None:
		self.opts['origin_colour']['value'] = colour
		self._updateOriginMarker()
		self.setViewBoxTransform()