import logging
import pathlib

import typing
from typing import Any

import imageio

from PyQt5 import QtCore, QtGui, QtWidgets

import vispy.app as app
from vispy.gloo.util import _screenshot

import satplot.model.data_models.data_types as data_types
from satplot.model.data_models.earth_raycast_data import EarthRayCastData
from satplot.model.data_models.history_data import HistoryData
from satplot.model.data_models.groundstation_data import GroundStationCollection
import satplot.visualiser.contexts.base_context as base
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
from satplot.visualiser.contexts.canvas_wrappers.cw_container import CWContainer
import satplot.visualiser.contexts.canvas_wrappers.history2d_cw as history2d_cw
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.controls as controls
import satplot.visualiser.interface.dialogs as dialogs
import satplot.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class History2DContext(base.BaseContext):
	data_type = [data_types.DataType.HISTORY]

	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow,
					history_data:HistoryData,
					groundstation_data:GroundStationCollection,
					raycast_data:EarthRayCastData):
		super().__init__(name)
		self.window = parent_window
		self.data: dict[str, Any] = {}
		self.data['history'] = history_data
		self.data['groundstations'] = groundstation_data
		self.data['raycast_src'] = raycast_data
		self._validateDataType()
		self.canvas_wrapper = history2d_cw.History2DCanvasWrapper()
		self.canvas_wrapper.setModel(self.data['history'], self.data['groundstations'], self.data['raycast_src'])
		self.controls = Controls(self, self.canvas_wrapper)

		disp_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
		disp_hsplitter.setObjectName('disp_hsplitter')
		disp_hsplitter.setStyleSheet('''
					QSplitter#disp_hsplitter::handle {
								background-color: #DCDCDC;
							}
							''')
		content_widget = QtWidgets.QWidget()
		content_vlayout = QtWidgets.QVBoxLayout()
		
		# Build display area layout
		'''
		# | ###
		# | ###
		# | ###
		'''
		disp_hsplitter.addWidget(self.controls.config_tabs)
		self.cw_container = CWContainer()
		self.cw_container.addWidget(self.canvas_wrapper.getCanvas().native)
		disp_hsplitter.addWidget(self.cw_container)
		# Build area down to bottom of time slider
		'''
		# | ###
		# | ###
		# | ###
		#######
		'''
		content_vlayout.addWidget(disp_hsplitter)
		content_vlayout.addWidget(self.controls.time_slider)
		content_widget.setLayout(content_vlayout)

		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(content_widget)

	def connectControls(self) -> None:
		logger.info("Connecting controls of %s", self.config['name'])
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['save-gif']['callback'] = self.setupGIFDialog
		self.controls.action_dict['save-screenshot']['callback'] = self.setupScreenshot
		if self.data['history'] is None:
			logger.warning('Context History3D: %s does not have a data model.', self)
			raise AttributeError(f'Context History3D: {self} does not have a data model.')
		self.data['history'].data_ready.connect(self._procDataUpdated)
		self.cw_container.left.connect(self.canvas_wrapper.stopMouseOverTimer)

	def _validateDataType(self) -> None:
		if self.data['history'] is not None and self.data['history'].getType() != self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['history'].getType()}")
			console.sendErr(f"\t should be: {self.data_type}")

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.blockSignals(True)
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_slider._curr_dt_picker.setDatetime(self.data['history'].getTimespan().start)
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))
		self.controls.time_slider.blockSignals(False)

	def _updateDataSources(self) -> None:
		# self.data['groundstations'].updateTimespans(self.data['history'].timespan)
		self.canvas_wrapper.modelUpdated()
		self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data['history'] is None:
			logger.warning("model history data is not set for context %s:%s", self.config['name'], self)
			ValueError(f"model history data is not set for context {self.config['name']}:{self}")
		self.canvas_wrapper.updateIndex(index)
		self.data['history'].updateIndex(index)
		self.canvas_wrapper.recomputeRedraw()

	def _procDataUpdated(self):
		self._updateControls()
		self._updateDataSources()

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

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['data'] = self.data['history'].prepSerialisation()
		state['controls'] = self.controls.prepSerialisation()
		state['camera'] = self.canvas_wrapper.prepSerialisation()
		return state

	def _centerCameraEarth(self) -> None:
		self.canvas_wrapper.centerCameraEarth()

	def saveGif(self, file:pathlib.Path, loop=True, camera_adjustment_data=None, start_index=0, end_index=-1):
		# TODO: need to lockout controls
		console.send('Starting GIF saving, please do not touch the controls.')
		max_num_steps = self.controls.time_slider.num_ticks
		start_idx = max(0, min(start_index, max_num_steps))
		if end_index == -1:
			end_index = max_num_steps
		end_idx = max(start_idx, min(end_index, max_num_steps))

		if loop:
			num_loops = 0
		else:
			num_loops = 1

		writer = imageio.get_writer(file, loop=num_loops)

		# calculate viewport of just the canvas
		geom = self.canvas_wrapper.canvas.native.geometry()
		ratio = self.canvas_wrapper.canvas.native.devicePixelRatio()
		geom = (geom.x(), geom.y(), geom.width(), geom.height())
		new_pos = self.canvas_wrapper.canvas.native.mapTo(self.window, QtCore.QPoint(0, 0))
		new_y = self.window.height() - (new_pos.y() + geom[3])
		viewport = (new_pos.x() * ratio, new_y * ratio, geom[2] * ratio, geom[3] * ratio)

		for ii in range(start_idx, end_idx):
			self.controls.time_slider.setValue(ii)
			app.process_events()

			im = _screenshot(viewport=viewport)
			writer.append_data(im)
			# use this to print to console on last iteration, otherwise thread doesn't get serviced until after writer closes
			if ii==end_idx-1:
				console.send("Writing file. Please wait...")
				app.process_events()

		writer.close()
		self.controls.time_slider.setValue(start_idx)
		console.send(f"Saved {self.config['name']} GIF to {file}")

	def setupGIFDialog(self):
		dflt_camera_setup = {}
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
		self.shortcuts={}
		self.shortcuts['PgDown'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgDown'), self.context.widget)
		self.shortcuts['PgDown'].activated.connect(self.time_slider.incrementValue)
		self.shortcuts['PgUp'] = QtWidgets.QShortcut(QtGui.QKeySequence('PgUp'), self.context.widget)
		self.shortcuts['PgUp'].activated.connect(self.time_slider.decrementValue)
		self.shortcuts['Home'] = QtWidgets.QShortcut(QtGui.QKeySequence('Home'), self.context.widget)
		self.shortcuts['Home'].activated.connect(self.time_slider.setBeginning)
		self.shortcuts['End'] = QtWidgets.QShortcut(QtGui.QKeySequence('End'), self.context.widget)
		self.shortcuts['End'].activated.connect(self.time_slider.setEnd)

	def _connectSliderCamUpdate(self):
		self.time_slider.slider.valueChanged.connect(self._updateCam)

	def _updateCam(self):
		if self.context.sccam_state and self.context.canvas_wrapper is not None:
			self.context.canvas_wrapper.centerCameraSpacecraft(set_zoom=False)

	def getCurrIndex(self):
		return self.time_slider.getValue()

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