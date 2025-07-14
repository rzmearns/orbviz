import datetime as dt
import imageio
import pathlib
import logging
import sys
from typing import Any

from vispy.gloo.util import _screenshot
import vispy.app as app

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot.model.data_models.data_types as data_types
from satplot.model.data_models.history_data import HistoryData
import satplot.util.paths as paths
import satplot.visualiser.contexts.base_context as base
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)
import satplot.visualiser.contexts.canvas_wrappers.history3d_cw as history3d_cw
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.dialogs as dialogs
import satplot.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class History3DContext(base.BaseContext):
	data_type = data_types.DataType.HISTORY

	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow, history_data:HistoryData):
		# super().__init__(name, data)
		super().__init__(name)
		self.window = parent_window
		self._validateDataType()
		# self.data = data
		self.data: dict[str,Any] = {}
		self.data['history'] = history_data
		self.canvas_wrapper = history3d_cw.History3DCanvasWrapper()
		# self.canvas_wrapper.setModel(self.data)
		self.canvas_wrapper.setModel(self.data['history'])
		self.controls = Controls(self, self.canvas_wrapper)

		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
								background-color: #DCDCDC;
							}
							''')
		self.content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()
		
		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		disp_hsplitter.addWidget(self.canvas_wrapper.getCanvas().native)

		# Build area down to bottom of time slider
		'''
		# | ###
		# | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addWidget(self.controls.time_slider)
		self.content_widget.setLayout(content_vlayout)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(self.content_widget)

	def connectControls(self) -> None:
		logger.info(f"Connecting controls of {self.config['name']}")
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['center-spacecraft']['callback'] = self._toggleCameraSpacecraft
		self.controls.action_dict['save-gif']['callback'] = self.setupGIFDialog
		self.controls.action_dict['save-screenshot']['callback'] = self.setupScreenshot
		self.sccam_state = False
		if self.data is None:
			logger.warning(f'Context History3D: {self} does not have a data model.')
			raise AttributeError(f'Context History3D: {self} does not have a data model.')
		self.data['history'].data_ready.connect(self._updateDataSources)
		self.data['history'].data_ready.connect(self._updateControls)

	def _validateDataType(self) -> None:
		if self.data is not None and self.data['history'].getType() != self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['history'].getType()}")
			console.sendErr(f"\t should be: {self.data_type}")

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data['history'].getTimespan().start)
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))

	def _updateDataSources(self) -> None:
		self.canvas_wrapper.modelUpdated()
		self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data is None:
			logger.warning(f"model data is not set for context {self.config['name']}:{self}")
			ValueError(f"model data is not set for context {self.config['name']}:{self}")
		self.canvas_wrapper.updateIndex(index)
		self.data['history'].updateIndex(index)
		self.canvas_wrapper.recomputeRedraw()

	def loadState(self) -> None:
		pass

	def saveState(self) -> None:
		pass

	def getIndex(self) -> int|None:
		return self.controls.time_slider.getValue()

	def setIndex(self, idx:int) -> None:
		self.controls.time_slider.setValue(idx)

	def deSerialise(self, state_dict: dict[str, Any]) -> None:
		self.data['history'].deSerialise(state_dict['data'])
		self._updateDataSources()
		self.canvas_wrapper.deSerialise(state_dict['camera'])
		self.controls.deSerialise(state_dict['controls'])

		# self.data = state_dict['data']
		# self.canvas_wrapper.setSource(self.data['timespan'],
		# 								self.data['orbit'],
		# 								self.data['pointing'],
		# 								self.data['pointing_invert_transform'],
		# 								self.data['constellation_list'],
		# 								self.data['constellation_beam_angle'])
		# self.canvas_wrapper.setFirstDrawFlags()
		# console.send(f"Drawing {self.data['name']} Assets...")

		# self.canvas_wrapper.deSerialise(state_dict['camera'])

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['data'] = self.data['history'].prepSerialisation()
		state['controls'] = self.controls.prepSerialisation()
		state['camera'] = self.canvas_wrapper.prepSerialisation()
		return state



	def _centerCameraEarth(self) -> None:
		if self.sccam_state and self.controls.toolbar.button_dict['center-spacecraft'].isChecked():
			# if center cam on sc is on, turn it off when selecting center cam on earth.
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(False)
		self.sccam_state = False
		self.canvas_wrapper.centerCameraEarth()	

	def _toggleCameraSpacecraft(self) -> None:
		self.sccam_state = not self.sccam_state

		if self.sccam_state:
			self.canvas_wrapper.centerCameraSpacecraft()
			# setting button to checkable in case camera set to center via menu
			self.controls.toolbar.button_dict['center-spacecraft'].setChecked(True)



	def saveGif(self, file:pathlib.Path, loop=True, camera_adjustment_data={'az_start':0,
																			'el_start':0,
																			'az_range':0,
																			'el_range':0},
																			start_index=0, end_index=-1):
		# TODO: need to lockout controls
		print(f'Creating Gif')

		# print(f'\t{file=}')
		# print(f'\t{loop=}')
		# print(f'\t{start_azimuth=}')
		# print(f'\t{azimuth_total_range=}')
		# print(f'\t{start_elevation=}')
		# print(f'\t{elevation_total_range=}')
		# print(f'\t{start_index=}')
		# print(f'\t{end_index=}')

		max_num_steps = self.controls.time_slider.num_ticks
		start_idx = max(0, min(start_index, max_num_steps))
		if end_index == -1:
			end_index = max_num_steps
		end_idx = max(start_idx, min(end_index, max_num_steps))

		num_steps = end_idx - start_idx

		start_azimuth = camera_adjustment_data['az_start']
		start_elevation = camera_adjustment_data['el_start']

		azimuth_step_angle = camera_adjustment_data['az_range']/num_steps
		elevation_step_angle = camera_adjustment_data['el_range']/num_steps

		if loop:
			num_loops = 0
		else:
			num_loops = 1

		# print(f'\t{num_loops=}')
		# print(f'\t{start_azimuth=}')
		# print(f'\t{azimuth_step_angle=}')
		# print(f'\t{start_elevation=}')
		# print(f'\t{elevation_step_angle=}')
		# print(f'\t{start_idx=}')
		# print(f'\t{end_idx=}')

		writer = imageio.get_writer(file, loop=num_loops)

		# calculate viewport of just the canvas
		geom = self.canvas_wrapper.canvas.native.geometry()
		ratio = self.canvas_wrapper.canvas.native.devicePixelRatio()
		geom = (geom.x(), geom.y(), geom.width(), geom.height())
		new_pos = self.canvas_wrapper.canvas.native.mapTo(self.window, QtCore.QPoint(0, 0))
		new_y = self.window.height() - (new_pos.y() + geom[3])
		viewport = (new_pos.x() * ratio, new_y * ratio, geom[2] * ratio, geom[3] * ratio)

		for ii in range(num_steps):

			self.canvas_wrapper.view_box.camera.azimuth = start_azimuth - ii*azimuth_step_angle
			self.canvas_wrapper.view_box.camera.elevation = start_elevation - ii*elevation_step_angle
			self.controls.time_slider.setValue(ii)
			app.process_events()

			im = _screenshot(viewport=viewport)
			writer.append_data(im)


		writer.close()
		self.canvas_wrapper.view_box.camera.azimuth = start_azimuth
		self.canvas_wrapper.view_box.camera.elevation = start_elevation
		self.controls.time_slider.setValue(start_idx)
		print(f'Finished creating GIF')

	def setupGIFDialog(self):
		print(self.canvas_wrapper.view_box.camera)
		print(self.canvas_wrapper.view_box.camera.name)
		dflt_camera_setup = {'az_start':self.canvas_wrapper.view_box.camera.azimuth,
							'el_start':self.canvas_wrapper.view_box.camera.elevation}
		timespan_max_range = self.controls.time_slider.num_ticks
		dialogs.GIFDialog(self.window,
							self,
							self.canvas_wrapper.view_box.camera.name,
							dflt_camera_setup,
							timespan_max_range)

		
class Controls(base.BaseControls):
	def __init__(self, parent_context:base.BaseContext, canvas_wrapper:BaseCanvas):
		self.context = parent_context
		self.cw = canvas_wrapper
		super().__init__(self.context.config['name'])
		# Prep config widgets
		self.config_controls = controls.OptionConfigs(self.cw.assets)

		# Wrap config widgets in tabs
		self.config_tabs = QtWidgets.QTabWidget()
		self.config_tabs.addTab(self.config_controls, 'Visual Options')

		# Prep time slider
		self.time_slider = widgets.TimeSlider()
		self.time_slider.setFixedHeight(50)

		# Prep toolbars
		self.toolbar = controls.Toolbar(self.context.window, self.action_dict, context_name=self.context.config['name'])
		self.menubar = controls.Menubar(self.context.window, self.action_dict, context_name=self.context.config['name'])

		self.setHotkeys()
		self._connectSliderCamUpdate()

	def setHotkeys(self):
		self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.widget)
		self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
		self.shortcuts['PgDown'].activated.connect(self._updateCam)
		self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.widget)
		self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
		self.shortcuts['PgUp'].activated.connect(self._updateCam)
		self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.widget)
		self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
		self.shortcuts['Home'].activated.connect(self._updateCam)
		self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.widget)
		self.shortcuts['End'].activated.connect(self.time_slider.setEnd)
		self.shortcuts['End'].activated.connect(self._updateCam)
		# self.shortcuts['F12'] = QtWidgets.QShortcut(QtGui.QKeySequence('F12'), self.context.window)
		# self.shortcuts['F12'].activated.connect(self.context.setupGIFDialog)

	def getCurrIndex(self) -> int:
		return self.time_slider.getValue()

	def _connectSliderCamUpdate(self):
		self.time_slider.slider.valueChanged.connect(self._updateCam)

	def _updateCam(self):
		if self.context.sccam_state and self.context.canvas_wrapper is not None:
			self.context.canvas_wrapper.centerCameraSpacecraft(set_zoom=False)

	def prepSerialisation(self):
		state = {}
		state['config_controls'] = self.config_controls.prepSerialisation()
		state['time_slider'] = self.time_slider.prepSerialisation()
		return state

	def deSerialise(self, state):
		self.time_slider.deSerialise(state['time_slider'])
		self.config_controls.deSerialise(state['config_controls'])


	def rebuildOptions(self):
		self.config_controls.rebuild()