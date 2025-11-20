import logging

from typing import Any

from PyQt5 import QtCore, QtGui, QtWidgets

import orbviz.model.data_models.data_types as data_types
from orbviz.model.data_models.groundstation_data import GroundStationCollection
from orbviz.model.data_models.history_data import HistoryData
import orbviz.util.gifs as gifs
import orbviz.visualiser.cameras.cam_utility_types as cam_utility_types
import orbviz.visualiser.contexts.base_context as base
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import orbviz.visualiser.contexts.canvas_wrappers.history3d_cw as history3d_cw
import orbviz.visualiser.interface.console as console
import orbviz.visualiser.interface.controls as controls
import orbviz.visualiser.interface.dialogs as dialogs
import orbviz.visualiser.interface.widgets as widgets

logger = logging.getLogger(__name__)

class History3DContext(base.BaseContext):
	data_type = data_types.DataType.HISTORY

	def __init__(self, name:str, parent_window:QtWidgets.QMainWindow,
						history_data:HistoryData,
						groundstation_data:GroundStationCollection):
		# super().__init__(name, data)
		super().__init__(name)
		self.window = parent_window
		self._validateDataType()
		# self.data = data
		self.data: dict[str,Any] = {}
		self.data['history'] = history_data
		self.data['groundstations'] = groundstation_data
		self.canvas_wrapper = history3d_cw.History3DCanvasWrapper()
		# self.canvas_wrapper.setModel(self.data)
		self.canvas_wrapper.setModel(self.data['history'], self.data['groundstations'])
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
		logger.info("Connecting controls of %s", self.config['name'])
		self.controls.time_slider.add_connect(self._updateDisplayedIndex)
		self.controls.action_dict['center-earth']['callback'] = self._centerCameraEarth
		self.controls.action_dict['center-spacecraft']['callback'] = self._toggleCameraSpacecraft
		self.controls.action_dict['save-gif']['callback'] = self.setupGIFDialog
		self.controls.action_dict['save-screenshot']['callback'] = self.setupScreenshot
		self.sccam_state = False

	def _validateDataType(self) -> None:
		if self.data is not None and self.data['history'].getType() != self.data_type:
			console.sendErr(f"Error: history3D context has wrong data type: {self.data['history'].getType()}")
			console.sendErr(f"\t should be: {self.data_type}")

	def _updateControls(self, *args, **kwargs) -> None:
		self.controls.time_slider.blockSignals(True)
		self.controls.time_slider.setTimespan(self.data['history'].getTimespan())
		self.controls.time_slider.setValue(int(self.controls.time_slider.num_ticks/2))
		self.controls.time_slider.blockSignals(False)

	def _updateDataSources(self) -> None:
		# self.data['groundstations'].updateTimespans(self.data['history'].timespan)
		self.canvas_wrapper.modelUpdated()
		self.controls.rebuildOptions()
		self.canvas_wrapper.setFirstDrawFlags()
		self._updateDisplayedIndex(self.controls.time_slider.slider.value())

	def _updateDisplayedIndex(self, index:int) -> None:
		if self.data is None:
			logger.warning("model data is not set for context %s:%s", self.config['name'], self)
			ValueError(f"model data is not set for context {self.config['name']}:{self}")
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



	# def abortGIF(self):


	def setupGIFDialog(self):
		# add check that timespan is not None
		cam_config = cam_utility_types.TurntableCameraAdjustment(az_start=self.canvas_wrapper.view_box.camera.azimuth,
															el_start=self.canvas_wrapper.view_box.camera.elevation)

		gif_config = gifs.GIFConfig(self.data['history'].timespan,
											cam_config=cam_config)

		self._gif_data['abort_dialog'] = dialogs.AbortGIFDialog(self.window, self)
		self._gif_data['setup_dialog'] = dialogs.GIFDialog(self.window, self, gif_config)
		
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