import datetime as dt
import logging
import math
import pathlib

import typing
from typing import Any

from spherapy.timespan import TimeSpan

from PyQt5 import QtCore, QtGui, QtWidgets

import satplot.model.data_models.data_types as satplot_data_types
import satplot.util.paths as satplot_paths
import satplot.visualiser.colours as colours

logger = logging.getLogger(__name__)

class TimeSlider(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget|None=None, allow_no_callbacks=False) -> None:
		super().__init__(parent)
		self.start_dt = None
		self.end_dt = None
		self.range = 2*math.pi
		self.range_delta = None
		self.num_ticks = 1440
		self.tick_delta = None
		self._allow_no_callbacks = allow_no_callbacks
		self.range_per_tick = self.range/self.num_ticks
		self._callbacks = []
		self._timespan = None
		vlayout = QtWidgets.QVBoxLayout()
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(2,1,2,1)
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(2,1,2,1)
		hlayout3 = QtWidgets.QHBoxLayout()
		hlayout3.setSpacing(0)
		hlayout3.setContentsMargins(2,1,2,1)
		self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
		self._start_dt_label = QtWidgets.QLabel('-')
		self._end_dt_label = QtWidgets.QLabel('-')
		self._curr_dt_picker = SmallDatetimeEntry(self.start_dt)
		self._curr_dt_picker.updated.connect(self.setIndex2Datetime)
		self.setTimeLabels()

		self.slider.setMinimum(0)
		self.slider.setMaximum(self.num_ticks)
		self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
		self.slider.setTickInterval(1)
		hlayout2.addWidget(self._start_dt_label)
		hlayout2.addStretch()
		hlayout2.addWidget(self._curr_dt_picker)
		hlayout2.addStretch()
		hlayout2.addWidget(self._end_dt_label)
		hlayout3.addWidget(self.slider)
		vlayout.addLayout(hlayout2)
		vlayout.addLayout(hlayout3)
		self.slider.valueChanged.connect(self._run_callbacks)
		self.setLayout(vlayout)

	def setTimespan(self, timespan:TimeSpan):
		self._timespan = timespan
		self.setRange(self._timespan.start, self._timespan.end, len(self._timespan))

	def setRange(self, start_dt, end_dt, num_ticks):
		if start_dt > end_dt:
			logger.warning("Period End %s must be after Period Start %s when setting timeslider range.", end_dt, start_dt)
			raise ValueError(f"Period End {end_dt} must be after Period Start {start_dt} when setting timeslider range.")
		self.start_dt = start_dt.replace(tzinfo=None)
		self.end_dt = end_dt.replace(tzinfo=None)
		self.range_delta = end_dt - start_dt
		self.setTicks(num_ticks)
		self.tick_delta = dt.timedelta(seconds=(self.range_delta.total_seconds()/num_ticks))
		self.setTimeLabels()

	def getValue(self):
		return self.slider.value()

	def setValue(self, value):
		self.slider.setValue(value)

	def setEnd(self):
		self.slider.setValue(self.slider.maximum())

	def setBeginning(self):
		self.slider.setValue(0)

	def incrementValue(self):
		curr_val = self.getValue()
		if curr_val == self.slider.maximum():
			return
		else:
			self.setValue(curr_val+1)

	def decrementValue(self):
		curr_val = self.getValue()
		if curr_val == 0:
			return
		else:
			self.setValue(curr_val-1)

	def setTimeLabels(self):
		if self.start_dt is not None:
			self._start_dt_label.setText(self.start_dt.strftime("%Y-%m-%d   %H:%M:%S"))
		else:
			self._start_dt_label.setText('-')
		if self.end_dt is not None:
			self._end_dt_label.setText(self.end_dt.strftime("%Y-%m-%d   %H:%M:%S"))
		else:
			self._end_dt_label.setText('-')

	def setIndex2Datetime(self, datetime):
		if datetime < self.start_dt:
			prev_index = 0
		elif datetime > self.end_dt:
			prev_index = self.num_ticks
		else:
			prev_index = int((datetime-self.start_dt)/self.tick_delta)
		curr_datetime = self.start_dt + (prev_index*self.tick_delta)
		self._curr_dt_picker.setDatetime(curr_datetime)
		self.slider.setValue(prev_index)

	def getDatetime(self) -> dt.datetime:
		return self.curr_datetime

	def setTicks(self, num_ticks):
		self.num_ticks = num_ticks
		self.slider.setMaximum(self.num_ticks-1)

	def add_connect(self, callback):
		if self._allow_no_callbacks:
			logger.warning('A callback is being set on a Time Slider intended for no _callbacks')
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if self._timespan is not None:
			self._curr_dt_picker.setDatetime(self._timespan[self.slider.value()])
		elif self.tick_delta is not None:
			self._curr_dt_picker.setDatetime(self.start_dt + (self.slider.value()*self.tick_delta))
		else:
			return
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.slider.value())
		elif not self._allow_no_callbacks:
			logger.warning("No Time Slider callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'timeSlider'
		state['start_dt'] = self.start_dt
		state['end_dt'] = self.end_dt
		state['num_ticks'] = self.num_ticks
		state['curr_index'] = self.getValue()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'timeSlider':
			logger.error("%s state was serialised as a %s, is now a timeSlider", self, state['type'])
			return
		self.setRange(state['start_dt'], state['end_dt'], state['num_ticks'])
		self.setValue(state['curr_index'])

class SmallDatetimeEntry(QtWidgets.QWidget):
	updated = QtCore.pyqtSignal(dt.datetime)

	def __init__(self, dflt_datetime, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.datetime = dflt_datetime
		hlayout = QtWidgets.QHBoxLayout()
		hlayout.setSpacing(0)
		hlayout.setContentsMargins(2,1,2,1)

		self._mon_sp = QtWidgets.QLabel("-")
		self._day_sp = QtWidgets.QLabel("-")
		self._hr_sp = QtWidgets.QLabel("     ")
		self._min_sp = QtWidgets.QLabel(":")
		self._sec_sp = QtWidgets.QLabel(":")
		self._yr_text_box = QtWidgets.QLineEdit('-')
		self._mon_text_box = QtWidgets.QLineEdit('-')
		self._day_text_box = QtWidgets.QLineEdit('-')
		self._hr_text_box = QtWidgets.QLineEdit('-')
		self._min_text_box = QtWidgets.QLineEdit('-')
		self._sec_text_box = QtWidgets.QLineEdit('-')

		fixed_height = 20

		self._mon_sp = QtWidgets.QLabel("-")
		self._day_sp = QtWidgets.QLabel("-")
		self._hr_sp = QtWidgets.QLabel("     ")
		self._min_sp = QtWidgets.QLabel(":")
		self._sec_sp = QtWidgets.QLabel(":")
		self._yr_text_box = QtWidgets.QLineEdit('-')
		self._mon_text_box = QtWidgets.QLineEdit('-')
		self._day_text_box = QtWidgets.QLineEdit('-')
		self._hr_text_box = QtWidgets.QLineEdit('-')
		self._min_text_box = QtWidgets.QLineEdit('-')
		self._sec_text_box = QtWidgets.QLineEdit('-')

		fixed_height = 20

		self._yr_text_box.setFixedHeight(fixed_height)
		self._yr_text_box.setFixedWidth(40)
		self._mon_text_box.setFixedHeight(fixed_height)
		self._mon_text_box.setFixedWidth(25)
		self._day_text_box.setFixedHeight(fixed_height)
		self._day_text_box.setFixedWidth(25)
		self._hr_text_box.setFixedHeight(fixed_height)
		self._hr_text_box.setFixedWidth(25)
		self._min_text_box.setFixedHeight(fixed_height)
		self._min_text_box.setFixedWidth(25)
		self._sec_text_box.setFixedHeight(fixed_height)
		self._sec_text_box.setFixedWidth(25)

		hlayout.addStretch()
		hlayout.addWidget(self._yr_text_box)
		hlayout.addWidget(self._mon_sp)
		hlayout.addWidget(self._mon_text_box)
		hlayout.addWidget(self._day_sp)
		hlayout.addWidget(self._day_text_box)
		hlayout.addWidget(self._hr_sp)
		hlayout.addWidget(self._hr_text_box)
		hlayout.addWidget(self._min_sp)
		hlayout.addWidget(self._min_text_box)
		hlayout.addWidget(self._sec_sp)
		hlayout.addWidget(self._sec_text_box)
		hlayout.addStretch()

		self._yr_text_box.editingFinished.connect(self.updateDatetime)
		self._mon_text_box.editingFinished.connect(self.updateDatetime)
		self._day_text_box.editingFinished.connect(self.updateDatetime)
		self._hr_text_box.editingFinished.connect(self.updateDatetime)
		self._min_text_box.editingFinished.connect(self.updateDatetime)
		self._sec_text_box.editingFinished.connect(self.updateDatetime)

		self.setLayout(hlayout)

	def updateDatetime(self):
		dt_str = f"{self._yr_text_box.text()}-"+ \
		f"{self._mon_text_box.text()}-"+ \
		f"{self._day_text_box.text()} "+ \
		f"{self._hr_text_box.text()}:"+ \
		f"{self._min_text_box.text()}:"+ \
		f"{self._sec_text_box.text()}"
		try:
			self.datetime = dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
		except ValueError:
			self.setDatetime(self.datetime)
			return
		self.updated.emit(self.datetime)

	def setDatetime(self, datetime):
		self.datetime = datetime
		self._yr_text_box.setText(datetime.strftime("%Y"))
		self._mon_text_box.setText(datetime.strftime("%m"))
		self._day_text_box.setText(datetime.strftime("%d"))
		self._hr_text_box.setText(datetime.strftime("%H"))
		self._min_text_box.setText(datetime.strftime("%M"))
		self._sec_text_box.setText(datetime.strftime("%S"))

class ColourPicker(QtWidgets.QWidget):
	def __init__(self, label, dflt_col, parent: QtWidgets.QWidget|None=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.curr_rgb = dflt_col
		self.curr_hex = colours.rgb2hex(dflt_col)

		closed_layout = QtWidgets.QHBoxLayout()
		open_layout = QtWidgets.QHBoxLayout()
		# closed_layout.setSpacing(0)
		closed_layout.setContentsMargins(2,1,2,1)
		# open_layout.setSpacing(0)
		open_layout.setContentsMargins(2,1,2,1)

		self._label = QtWidgets.QLabel(label)
		self._colour_box = QtWidgets.QPushButton()
		self._colour_box.setStyleSheet(f"background-color : {self.curr_hex}")
		self._text_box = QtWidgets.QLineEdit(str(self.curr_rgb)[1:-1])
		self._text_box.setFixedHeight(20)
		self._text_box.setFixedWidth(100)
		self._colour_box.setFixedHeight(20)
		self._colour_box.setFixedWidth(20)


		closed_layout.addWidget(self._label)
		closed_layout.addWidget(self._colour_box)
		closed_layout.addWidget(self._text_box)


		self._colorpicker = QtWidgets.QColorDialog()
		self._colorpicker.setOptions(QtWidgets.QColorDialog.DontUseNativeDialog)
		self._colour_box.pressed.connect(self._colorpicker.open)
		self._colorpicker.colorSelected.connect(self._set_colour)
		self._text_box.textEdited.connect(self._run_callbacks)
		self._text_box.returnPressed.connect(self._run_callbacks)

		self.setLayout(closed_layout)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _set_colour(self, colour):
		self._text_box.setText(f'{colour.red()},{colour.green()},{colour.blue()}')
		self._run_callbacks()

	def _run_callbacks(self):
		rgb_str = self._text_box.text().split(',')
		self.curr_rgb = (int(rgb_str[0]), int(rgb_str[1]), int(rgb_str[2]))
		self.curr_hex = colours.rgb2hex(self.curr_rgb)
		self._colour_box.setStyleSheet(f"background-color: {self.curr_hex}")
		# self._colour_box.setStyleSheet(f"onClicked: forceActiveFocus()")
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.curr_rgb)
		else:
			logger.warning("No Colour Picker callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ColourPicker'
		state['value'] = self.curr_rgb
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ColourPicker':
			logger.error("%s state was serialised as a %s, is now a ColourPicker", self, state['type'])

		self._text_box.blockSignals(True)
		self.curr_rgb = state['value']
		self.curr_hex = colours.rgb2hex(state['value'])
		self._colour_box.setStyleSheet(f"background-color: {self.curr_hex}")
		self._text_box.setText(f"{state['value'][0]},{state['value'][1]},{state['value'][2]}")
		self._text_box.blockSignals(False)


class ValueSpinner(QtWidgets.QWidget):
	def __init__(self, label, dflt_val, integer=True, fraction=False, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.allow_float = not integer
		if fraction:
			self.allow_float = True

		if self.allow_float:
			self.curr_val = dflt_val
		else:
			self.curr_val = int(dflt_val)


		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins(2,1,2,1)

		self._label = QtWidgets.QLabel(label)
		if self.allow_float or fraction:
			self._val_box = QtWidgets.QDoubleSpinBox()
		else:
			self._val_box = QtWidgets.QSpinBox()
		if not fraction:
			self._val_box.setRange(1,1000000)
		else:
			self._val_box.setRange(0,1)
			self._val_box.setSingleStep(0.1)
		self._val_box.setValue(self.curr_val)
		self._val_box.setFixedWidth(80)
		self._val_box.setFixedHeight(20)

		layout.addWidget(self._label)
		layout.addWidget(self._val_box)

		self._val_box.textChanged.connect(self._run_callbacks)
		self._val_box.valueChanged.connect(self._run_callbacks)

		self.setLayout(layout)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):

		if self.allow_float:
			self.curr_val = self._val_box.value()
		else:
			self.curr_val = int(self._val_box.value())
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.curr_val)
		else:
			logger.warning("No Value Spinner callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ValueSpinner'
		state['value'] = self.curr_val
		state['allow_float'] = self.allow_float
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ValueSpinner':
			logger.error("%s state was serialised as a %s, is now a ValueSpinner", self, state['type'])

		self._val_box.blockSignals(True)
		self.curr_val = state['value']
		if self.allow_float:
			self._val_box.setValue(float(self.curr_val))
		else:
			self._val_box.setValue(int(self.curr_val))
		self._val_box.blockSignals(False)

class Button(QtWidgets.QWidget):
	def __init__(self, label, button_label, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		vlayout.setSpacing(0)
		hlayout1.setSpacing(0)
		hlayout2.setSpacing(0)
		hlayout1.setContentsMargins(0,1,0,1)
		hlayout2.setContentsMargins(0,1,10,1)

		if label is not None:
			self._label = QtWidgets.QLabel(label)
			hlayout1.addWidget(self._label)
			hlayout1.addStretch()
		else:
			hlayout1.addStretch()

		self._button = QtWidgets.QPushButton(button_label)
		hlayout2.addWidget(self._button)
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

		self._button.clicked.connect(self._run_callbacks)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback()
		else:
			logger.warning("No Button callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'Button'
		state['value'] = None
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'Button':
			logger.error("%s state was serialised as a , is now a Button", self, state['type'])

class ToggleBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_state, parent: QtWidgets.QWidget=None, label_bold=False) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.curr_state = dflt_state
		layout = QtWidgets.QHBoxLayout()
		layout.setSpacing(0)
		layout.setContentsMargins(2,1,2,1)

		if label is not None:
			self._label_font = QtGui.QFont()
			if label_bold:
				self._label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(self._label_font)
			layout.addWidget(self._label)
			layout.addStretch()

		self._checkbox = QtWidgets.QCheckBox()
		self._checkbox.setChecked(dflt_state)
		layout.addWidget(self._checkbox)
		self._checkbox.stateChanged.connect(self._run_callbacks)

		self.setLayout(layout)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self._checkbox.isChecked())
		else:
			logger.warning("No Toggle Box callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ToggleBox'
		state['value'] = self._checkbox.isChecked()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ToggleBox':
			logger.error("%s state was serialised as a %s, is now a ToggleBox", self, state['type'])
		self._checkbox.blockSignals(True)
		self._checkbox.setChecked(state['value'])
		self._checkbox.blockSignals(False)

	def setState(self, state:bool) -> None:
		self._checkbox.setChecked(state)

	def getState(self) -> bool:
		return self._checkbox.isChecked()

	def setLabel(self, new_label:str) -> None:
		self._label.setText(new_label)

class OptionBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_state=None, options_list=[], parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self._curr_index = 0
		if len(options_list) > 0:
			if options_list[0] != '':
				options_list.insert(0,'')
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		vlayout.setSpacing(0)
		hlayout1.setSpacing(0)
		hlayout2.setSpacing(0)
		hlayout1.setContentsMargins(0,1,0,1)
		hlayout2.setContentsMargins(0,1,10,1)

		if label is not None:
			self._label = QtWidgets.QLabel(label)
			hlayout1.addWidget(self._label)
			hlayout1.addStretch()
		else:
			hlayout1.addStretch()

		self._optionbox = NonScrollingComboBox()
		for item in options_list:
			self._optionbox.addItem(item)
		self._optionbox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
		hlayout2.addWidget(self._optionbox)
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

		self._optionbox.currentIndexChanged.connect(self._run_callbacks)
		self._optionbox.currentIndexChanged.connect(self.setCurrentIndex)

	def setCurrentIndex(self, idx:int) -> None:
		self._curr_index = idx

	def getCurrentIndex(self) -> int|None:
		if self._curr_index > 0:
			return self._curr_index-1
		else:
			return None

	def setContainingScrollWidget(self, scrollWidget):
		self._optionbox.setContainingScrollWidget(scrollWidget)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self, index):
		self._curr_index = index
		if self._curr_index == -1:
			return
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(index)

	def clear(self):
		self._optionbox.clear()

	def addItems(self, iterable):
		self._optionbox.addItems(iterable)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'OptionBox'
		curr_idx = self.getCurrentIndex()+1
		if curr_idx is None:
			state['value'] = None
		else:
			state['value'] = self._optionbox.getAllItems()[curr_idx]
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'OptionBox':
			logger.error("%s state was serialised as a %s, is now an OptionBox", self, state['type'])
			return
		if state['value'] is not None and state['value'] in self._optionbox.getAllItems():
			self._optionbox.setCurrentText(state['value'])
		else:
			logger.error("%s is not a local valid option. Displaying data, but can't set options.", state['value'])

class BasicOptionBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_option=None, options_list=[], parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self._curr_index = 0
		layout = QtWidgets.QHBoxLayout()
		layout.setContentsMargins(2,1,2,1)


		self._label = QtWidgets.QLabel(label)

		self._optionbox = NonScrollingComboBox()
		for item in options_list:
			self._optionbox.addItem(item)
		self._optionbox.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

		layout.addWidget(self._label)
		layout.addWidget(self._optionbox)

		self._optionbox.setCurrentIndex(options_list.index(dflt_option))
		self._optionbox.currentIndexChanged.connect(self._run_callbacks)
		self._optionbox.currentIndexChanged.connect(self.setCurrentIndex)

		self.setLayout(layout)

	def setCurrentIndex(self, idx:int) -> None:
		self._curr_index = idx

	def getCurrentIndex(self) -> int|None:
		if self._curr_index > 0:
			return self._curr_index-1
		else:
			return None

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self, index):
		self._curr_index = index
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(index)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'BasicOptionBox'
		curr_idx = self.getCurrentIndex()
		if curr_idx is None:
			state['value'] = None
		else:
			state['value'] = self._optionbox.getAllItems()[curr_idx]
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'BasicOptionBox':
			logger.error("%s state was serialised as a %s, is now an OptionBox", self, state['type'])
			return
		if state['value'] is not None and state['value'] in self._optionbox.getAllItems():
			self._optionbox.setCurrentText(state['value'])
		else:
			logger.error("%s is not a local valid option. Displaying data, but can't set options.", state['value'])

class FilePicker(QtWidgets.QWidget):
	def __init__(self, label,
						dflt_file='',
						dflt_dir=None,
						save=False,
						margins=[0,0,0,0],
						parent: QtWidgets.QWidget=None,
						width=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self._dflt_path = pathlib.Path(f'{dflt_dir}').joinpath(dflt_file)
		self.path = pathlib.Path(f'{dflt_dir}').joinpath(dflt_file)
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		vlayout.setSpacing(0)
		hlayout1.setSpacing(0)
		hlayout1.setContentsMargins(0,1,0,0)
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(0,0,10,1)
		vlayout.setContentsMargins(margins[0],margins[1],margins[2],margins[3])

		if label is not None:
			_label_font = QtGui.QFont()
			_label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(_label_font)
			hlayout1.addWidget(self._label)
			hlayout1.addStretch()
			vlayout.addLayout(hlayout1)

		# Create widgets
		path_to_show = self.path.relative_to(satplot_paths.data_dir)
		self._file_text_box = QtWidgets.QLineEdit(f'{path_to_show}')
		self._err_label = QtWidgets.QLabel('')
		self._dialog_button = QtWidgets.QPushButton('...')
		self._dialog_save_flag = save
		self._dialog_caption = f'Pick {label}'
		# Set styling
		self._dialog_button.setFixedWidth(25)
		err_font = QtGui.QFont()
		err_font.setBold(True)
		self._err_label.setFont(err_font)
		self._err_label.setStyleSheet('''
										QLabel {
												color:#FF0000;
												}
									''');

		hlayout2.addWidget(self._file_text_box)
		hlayout2.addSpacing(5)
		hlayout2.addWidget(self._dialog_button)
		vlayout.addLayout(hlayout2)
		vlayout.addWidget(self._err_label)
		self.setLayout(vlayout)

		self._dialog_button.clicked.connect(self.openFilenameDialog)
		self._file_text_box.textChanged.connect(self._setPath)
		self._file_text_box.textChanged.connect(self._run_callbacks)

	def _setPath(self):
		self.path = pathlib.Path(satplot_paths.data_dir.joinpath(self._file_text_box.text()))

	def setError(self, err_text:str) -> None:
		self._err_label.setText(err_text)

	def clearError(self) -> None:
		self._err_label.setText('')

	def getPath(self) -> pathlib.Path:
		return self.path

	def openFilenameDialog(self):
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		if self._dialog_save_flag:
			filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
																self._dialog_caption,
																str(self._dflt_path),
																"All Files (*)",
																options=options)
		else:
			filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
																self._dialog_caption,
																str(self._dflt_path),
																"All Files (*)",
																options=options)
		self._file_text_box.blockSignals(True)
		self.path = pathlib.Path(filename)
		if not self.path.exists():
			self.setError('File does not exist')
			path_good = False
		elif self.path.is_dir():
			self.setError('Cannot load directory')
			path_good = False
		else:
			self.clearError()
			path_good = True

		try:
			path_to_show = self.path.relative_to(satplot_paths.data_dir)
		except ValueError:
			path_to_show = self.path.resolve()
		self._file_text_box.setText(f'{path_to_show}')

		if path_good:
			self._run_callbacks()

		self._file_text_box.blockSignals(False)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.path)
		else:
			logger.warning("No FilePicker callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'filePicker'
		state['value'] = self.path
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'filePicker':
			logger.error("%s state was serialised as a %s, is now a filePicker", self, state['type'])
			return
		self._file_text_box.setText(state['value'])

class PeriodBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_val, parent: QtWidgets.QWidget=None):
		super().__init__(parent)
		self._callbacks = []
		self.period = dflt_val
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout1.setSpacing(0)
		hlayout1.setContentsMargins(2,1,2,1)
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(2,1,2,1)
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(2,1,2,1)

		if label is not None:
			self._label_font = QtGui.QFont()
			self._label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(self._label_font)
			hlayout1.addWidget(self._label)

		H,M,S = self.periodToHMS()
		self._hms_label = QtWidgets.QLabel(f'{H}hrs - {M}mins - {S}secs')
		self.val_box = QtWidgets.QSpinBox()
		self.val_box.setValue(self.period)
		self.val_box.setRange(1,86400)
		self.val_box.setFixedWidth(80)

		hlayout1.addWidget(self._hms_label)
		hlayout2.addWidget(self.val_box)
		hlayout2.addStretch()
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)

		self.val_box.textChanged.connect(self.updateLabels)
		self.val_box.valueChanged.connect(self.updateLabels)

		self.setLayout(vlayout)

	def updateLabels(self):
		self.period = int(self.val_box.text())
		H,M,S = self.periodToHMS()
		self._hms_label.setText(f'{H}hrs - {M}mins - {S}secs')

	def periodToHMS(self):
		H = int(self.period/3600)
		M = int((self.period-H*3600)/60)
		S = int(self.period-H*3600-M*60)

		return H,M,S

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'period'
		state['value'] = self.period
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'period':
			logger.error("%s state was serialised as a %s, is now a period", self, state['type'])
			return
		self.val_box.setValue(state['value'])

class DatetimeEntry(QtWidgets.QWidget):
	def __init__(self, label, dflt_datetime, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		# datetime should always be in UTC
		self.datetime = dflt_datetime.replace(tzinfo=dt.timezone.utc)
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout1.setSpacing(0)
		hlayout1.setContentsMargins(2,1,2,1)
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(2,1,2,1)
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(2,1,2,1)

		if label is not None:
			self._label_font = QtGui.QFont()
			self._label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(self._label_font)
			hlayout1.addWidget(self._label)

		self._curr_dt = QtWidgets.QLabel(self.datetime.strftime("%Y-%m-%d   %H:%M:%S UTC"))
		self._mon_sp = QtWidgets.QLabel("-")
		self._day_sp = QtWidgets.QLabel("-")
		self._hr_sp = QtWidgets.QLabel("     ")
		self._min_sp = QtWidgets.QLabel(":")
		self._sec_sp = QtWidgets.QLabel(":")
		self._yr_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%Y"))
		self._mon_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%m"))
		self._day_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%d"))
		self._hr_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%H"))
		self._min_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%M"))
		self._sec_text_box = QtWidgets.QLineEdit(self.datetime.strftime("%S"))

		# self._text_box.setFixedHeight(20)
		self._yr_text_box.setFixedWidth(40)
		self._mon_text_box.setFixedWidth(25)
		self._day_text_box.setFixedWidth(25)
		self._hr_text_box.setFixedWidth(25)
		self._min_text_box.setFixedWidth(25)
		self._sec_text_box.setFixedWidth(25)

		hlayout1.addWidget(self._curr_dt)
		hlayout2.addWidget(self._yr_text_box)
		hlayout2.addWidget(self._mon_sp)
		hlayout2.addWidget(self._mon_text_box)
		hlayout2.addWidget(self._day_sp)
		hlayout2.addWidget(self._day_text_box)
		hlayout2.addWidget(self._hr_sp)
		hlayout2.addWidget(self._hr_text_box)
		hlayout2.addWidget(self._min_sp)
		hlayout2.addWidget(self._min_text_box)
		hlayout2.addWidget(self._sec_sp)
		hlayout2.addWidget(self._sec_text_box)
		hlayout2.addStretch()

		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)


		self._yr_text_box.editingFinished.connect(self.updateDatetime)
		self._mon_text_box.editingFinished.connect(self.updateDatetime)
		self._day_text_box.editingFinished.connect(self.updateDatetime)
		self._hr_text_box.editingFinished.connect(self.updateDatetime)
		self._min_text_box.editingFinished.connect(self.updateDatetime)
		self._sec_text_box.editingFinished.connect(self.updateDatetime)

		self.setLayout(vlayout)

	def updateDatetime(self):
		dt_str = f"{self._yr_text_box.text()}-"+ \
		f"{self._mon_text_box.text()}-"+ \
		f"{self._day_text_box.text()} "+ \
		f"{self._hr_text_box.text()}:"+ \
		f"{self._min_text_box.text()}:"+ \
		f"{self._sec_text_box.text()}"
		try:
			self.datetime = dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
			self.datetime = self.datetime.replace(tzinfo=dt.timezone.utc)
		except ValueError:
			self.setDatetime(self.datetime)
			return
		self._curr_dt.setText(self.datetime.strftime("%Y-%m-%d   %H:%M:%S UTC"))

	def setDatetime(self, datetime):
		self.datetime = datetime.replace(tzinfo=dt.timezone.utc)
		self._yr_text_box.setText(datetime.strftime("%Y"))
		self._mon_text_box.setText(datetime.strftime("%m"))
		self._day_text_box.setText(datetime.strftime("%d"))
		self._hr_text_box.setText(datetime.strftime("%H"))
		self._min_text_box.setText(datetime.strftime("%M"))
		self._sec_text_box.setText(datetime.strftime("%S"))
		self._curr_dt.setText(self.datetime.strftime("%Y-%m-%d   %H:%M:%S UTC"))

	def addConnect(self, callback):
		self._callbacks.append(callback)

	def _runCallbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				pass
				# callback(self._checkbox.isChecked())
		else:
			logger.warning("No Toggle Box callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'DatetimeEntry'
		state['value'] = self.datetime
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'DatetimeEntry':
			logger.error("%s state was serialised as a %s, is now a DatetimeEntry", self, state['type'])
			return
		self.setDatetime(state['value'])

class ValueBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_value, parent: QtWidgets.QWidget=None, label_bold=False, margins=[2,1,2,1]) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.value = str(dflt_value)
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout1.setSpacing(0)
		hlayout1.setContentsMargins(margins[0],margins[1],margins[2],margins[3])
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(margins[0],margins[1],margins[2],margins[3])
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(margins[0],margins[1],margins[2],margins[3])

		if label is not None:
			self._label_font = QtGui.QFont()
			if label_bold:
				self._label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(self._label_font)
			hlayout1.addWidget(self._label)
		hlayout1.addStretch()
		vlayout.addLayout(hlayout1)

		self._val_text_box = QtWidgets.QLineEdit(self.value)

		hlayout2.addWidget(self._val_text_box)
		hlayout2.addStretch()

		vlayout.addLayout(hlayout2)

		self.setLayout(vlayout)
		self._val_text_box.editingFinished.connect(self._updateValue)


	def getValue(self) -> float:
		return float(self.value)

	def _updateValue(self):
		self.value = self._val_text_box.text()

	def setValue(self, val:float) -> None:
		self.value = str(val)
		self._val_text_box.setText(self.value)

	def addConnect(self, callback):
		self._callbacks.append(callback)

	def _runCallbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				pass
				# callback(self._checkbox.isChecked())
		else:
			logger.warning("No ValueBox callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ValueBox'
		state['value'] = str(self.value)
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ValueBox':
			logger.error("%s state was serialised as a %s, is now a ValueBox", self, state['type'])
			return
		self.setValue(state['value'])

class CollapsibleSection(QtWidgets.QWidget):
	# Ported to PyQT5 and modified, original widget by Caroline Beyne, github user: cbeyne
	# https://github.com/By0ute/pyqt-collapsible-widget/blob/master/code/FrameLayout.py
	def __init__(self, parent=None, title=None):
		QtWidgets.QFrame.__init__(self, parent=parent)

		self._is_collapsed = True
		self._title_frame = None
		self._content, self._content_layout = (None, None)

		self.v_layout = QtWidgets.QVBoxLayout(self)
		self.v_layout.addWidget(self.initTitleFrame(title, self._is_collapsed))
		self.v_layout.addWidget(self.initContent(self._is_collapsed))
		self.v_layout.setAlignment(QtCore.Qt.AlignLeft)
		self.v_layout.setSpacing(5)
		self._content_layout.setSpacing(5)
		self.v_layout.setContentsMargins(0,1,0,1)
		self._content_layout.setContentsMargins(20,1,0,1)
		self.initCollapsable()

	def initTitleFrame(self, title, collapsed):
		self._title_frame = self.TitleButton(title=title, collapsed=collapsed)

		return self._title_frame

	def initContent(self, collapsed):
		self._content = QtWidgets.QWidget()
		self._content_layout = QtWidgets.QVBoxLayout()
		self._content_layout.setAlignment(QtCore.Qt.AlignLeft)
		self._content.setLayout(self._content_layout)
		self._content.setVisible(not collapsed)

		return self._content

	def addWidget(self, widget):
		self._content_layout.addWidget(widget)
		# widget.setAlignment(QtCore.Qt.AlignLeft)

	def initCollapsable(self):
		self._title_frame._button.pressed.connect(self.toggleCollapsed)

	def toggleCollapsed(self):
		self._content.setVisible(self._is_collapsed)
		self._content_layout.setAlignment(QtCore.Qt.AlignLeft)
		self.v_layout.setAlignment(QtCore.Qt.AlignLeft)
		self._is_collapsed = not self._is_collapsed

	def setCollapsed(self, state:bool):

		if state:
			# collapsed
			self._is_collapsed = True
			self._content.setVisible(False)
		else:
			self._is_collapsed = False
			self._content.setVisible(True)
			self._content_layout.setAlignment(QtCore.Qt.Alignment.AlignLeft)
			self.v_layout.setAlignment(QtCore.Qt.Alignment.AlignLeft)

	class TitleButton(QtWidgets.QWidget):
		def __init__(self, parent=None, title="", collapsed=False):
			QtWidgets.QWidget.__init__(self, parent=parent)

			self._hlayout = QtWidgets.QHBoxLayout(self)
			self._hlayout.setContentsMargins(0, 0, 0, 0)
			self._hlayout.setSpacing(0)

			self._button = None
			self._hlayout.addWidget(self.initTitle(title))
			self._hlayout.addStretch()

		def initTitle(self, title=None):
			self._button = QtWidgets.QToolButton(text=title, checkable=True, checked=False)
			self._button.setStyleSheet('''
					QToolButton {
								border: 0px solid;
								text-align: left
							}
							  ''')
			self._button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
			self._button.setArrowType(QtCore.Qt.RightArrow)
			self._button.pressed.connect(self.on_pressed)
			return self._button

		@QtCore.pyqtSlot()
		def on_pressed(self):
			checked = self._button.isChecked()
			if checked:
				self._button.setArrowType(QtCore.Qt.RightArrow)
			else:
				self._button.setArrowType(QtCore.Qt.DownArrow)

class LabelledSwitch(QtWidgets.QWidget):
	toggle = QtCore.pyqtSignal(bool)

	def __init__(self, dflt_state:bool=True, labels:tuple[str,str]=('',''), *args, **kwargs):
		super().__init__()
		switch_hlayout = QtWidgets.QHBoxLayout()
		switch_hlayout.setSpacing(10)
		switch_hlayout.setContentsMargins(0,0,0,0)

		_off_label = QtWidgets.QLabel(labels[0])
		_on_label = QtWidgets.QLabel(labels[1])
		self._switch = Switch(dflt_state=dflt_state)

		switch_hlayout.addWidget(_off_label)
		switch_hlayout.addWidget(self._switch)
		switch_hlayout.addWidget(_on_label)
		switch_hlayout.addStretch()

		self.setLayout(switch_hlayout)

		self._switch.toggled.connect(self.toggle.emit)

	def isChecked(self) -> bool:
		return self._switch.isChecked()

class Switch(QtWidgets.QPushButton):

	def __init__(self, dflt_state:bool=True, parent = None):
		super().__init__(parent)
		self.setCheckable(True)
		self.setChecked(dflt_state)
		self.setMinimumWidth(66)
		self.setMinimumHeight(22)

	def paintEvent(self, event):
		on_colour = QtGui.QColor(36,160,237)
		on_dis_colour = QtGui.QColor(161,202,227)
		off_colour = QtCore.Qt.gray
		if self.isEnabled():
			bg_colour = on_colour if self.isChecked() else off_colour
		else:
			bg_colour = on_dis_colour if self.isChecked() else off_colour
		sw_colour = QtCore.Qt.lightGray
		radius = 10
		width = 25
		center = self.rect().center()

		painter = QtGui.QPainter(self)
		painter.setRenderHint(QtGui.QPainter.Antialiasing)
		painter.translate(center)
		painter.setBrush(bg_colour)

		pen = QtGui.QPen(bg_colour)
		pen.setWidth(2)
		painter.setPen(pen)

		bg_rect = QtCore.QRect(-width, -radius, 2*width, 2*radius)
		painter.drawRoundedRect(bg_rect, radius, radius)
		painter.setBrush(QtGui.QBrush(sw_colour))
		sw_rect = QtCore.QRect(-radius, -radius, 2*radius, 2*radius)

		if self.isChecked():
			sw_rect.moveTo(width-2*radius,-radius)
		else:
			sw_rect.moveTo(-width,-radius)

		painter.drawRoundedRect(sw_rect, radius, radius)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'Switch'
		state['value'] = self.isChecked()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'Switch':
			logger.error("%s state was serialised as a %s, is now a Switch", self, state['type'])
			return
		self.setChecked(state['value'])

class NonScrollingComboBox(QtWidgets.QComboBox):
	def __init__(self, scrollWidget=None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.scrollWidget=scrollWidget
		self.setFocusPolicy(QtCore.Qt.StrongFocus)

	def getAllItems(self) -> list[str]:
		return [self.itemText(ii) for ii in range(self.count())]

	def setContainingScrollWidget(self, scrollwidget):
		self.scrollWidget = scrollwidget

	def wheelEvent(self, *args, **kwargs):
		if self.view().isVisible():
		# self.hasFocus():
			return QtWidgets.QComboBox.wheelEvent(self, *args, **kwargs)
		elif self.scrollWidget is not None:
			return self.scrollWidget.wheelEvent(*args, **kwargs)

class RangeSlider(QtWidgets.QSlider):
	sliderMoved = QtCore.pyqtSignal(int, int)

	""" A slider for ranges.

		This class provides a dual-slider for ranges, where there is a defined
		maximum and minimum, as is a normal slider, but instead of having a
		single slider value, there are 2 slider values.

		This class emits the same signals as the QSlider base class, with the
		exception of valueChanged
	"""
	def __init__(self, *args):
		super().__init__(*args)

		self._low = self.minimum()
		self._high = self.maximum()

		self.pressed_control = QtWidgets.QStyle.SC_None
		self.tick_interval = 0
		self.tick_position = QtWidgets.QSlider.NoTicks
		self.hover_control = QtWidgets.QStyle.SC_None
		self.click_offset = 0

		# 0 for the low, 1 for the high, -1 for both
		self.active_slider = 0

		self.start_stylesheet = '''
						QSlider::handle:horizontal {
							background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #40cc40, stop:1 #78cc78);
							border: 1px solid #5c5c5c;
							width: 18px;
							margin: -2px 0;
							border-radius: 3px;}
    							'''

		self.end_stylesheet = '''
						QSlider::handle:horizontal {
							background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff4040, stop:1 #ff7878);
							border: 1px solid #5c5c5c;
							width: 18px;
							margin: -2px 0;
							border-radius: 3px;}
    							'''

	def low(self):
		return self._low

	def setLow(self, low:int):
		self._low = low
		self.update()

	def high(self):
		return self._high

	def setHigh(self, high):
		self._high = high
		self.update()

	def getRange(self) -> tuple[int,int]:
		return self.low(), self.high()

	def paintEvent(self, event):
		# based on http://qt.gitorious.org/qt/qt/blobs/master/src/gui/widgets/qslider.cpp

		painter = QtGui.QPainter(self)
		style = self.style()

		# draw groove
		opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt)
		opt.siderValue = 0
		opt.sliderPosition = 0
		opt.subControls = QtWidgets.QStyle.SC_SliderGroove

		# if self.tickPosition() != self.NoTicks:
		opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks

		style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)
		groove = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self)

		# drawSpan
		#opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt)
		opt.subControls = QtWidgets.QStyle.SC_SliderGroove
		if self.tickPosition() != self.NoTicks:
		   opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks
		opt.siderValue = 0
		#print(self._low)
		opt.sliderPosition = self._low
		low_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)
		opt.sliderPosition = self._high
		high_rect = style.subControlRect(QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self)

		#print(low_rect, high_rect)
		low_pos = self.__pick(low_rect.center())
		high_pos = self.__pick(high_rect.center())

		min_pos = min(low_pos, high_pos)
		max_pos = max(low_pos, high_pos)

		c = QtCore.QRect(low_rect.center(), high_rect.center()).center()
		#print(min_pos, max_pos, c)
		if opt.orientation == QtCore.Qt.Horizontal:
			span_rect = QtCore.QRect(QtCore.QPoint(min_pos, c.y()-2), QtCore.QPoint(max_pos, c.y()+1))
		else:
			span_rect = QtCore.QRect(QtCore.QPoint(c.x()-2, min_pos), QtCore.QPoint(c.x()+1, max_pos))

		#self.initStyleOption(opt)
		#print(groove.x(), groove.y(), groove.width(), groove.height())
		if opt.orientation == QtCore.Qt.Horizontal: groove.adjust(0, 0, -1, 0)
		else: groove.adjust(0, 0, 0, -1)

		if True: #self.isEnabled():
			highlight = self.palette().color(QtGui.QPalette.Highlight)
			# highlight.setAlpha(255)
			painter.setBrush(QtGui.QBrush(highlight))
			painter.setPen(QtGui.QPen(highlight, 0))
			painter.setPen(QtGui.QPen(self.palette().color(QtGui.QPalette.Light), 0))
			'''
			if opt.orientation == QtCore.Qt.Horizontal:
				self.setupPainter(painter, opt.orientation, groove.center().x(), groove.top(), groove.center().x(), groove.bottom())
			else:
				self.setupPainter(painter, opt.orientation, groove.left(), groove.center().y(), groove.right(), groove.center().y())
			'''
			#spanRect =
			painter.drawRect(span_rect.intersected(groove))
			#painter.drawRect(groove)

		for i, value in enumerate([self._low, self._high]):
			opt = QtWidgets.QStyleOptionSlider()
			self.initStyleOption(opt)

			# Only draw the groove for the first slider so it doesn't get drawn
			# on top of the existing ones every time
			if i == 0:
				opt.subControls = QtWidgets.QStyle.SC_SliderHandle# | QtWidgets.QStyle.SC_SliderGroove
			else:
				opt.subControls = QtWidgets.QStyle.SC_SliderHandle

			if self.tickPosition() != self.NoTicks:
				opt.subControls |= QtWidgets.QStyle.SC_SliderTickmarks

			if self.pressed_control:
				opt.activeSubControls = self.pressed_control
			else:
				opt.activeSubControls = self.hover_control

			opt.sliderPosition = value
			opt.sliderValue = value
			if i == 0:
				self.setStyleSheet(self.start_stylesheet)
			else:
				self.setStyleSheet(self.end_stylesheet)
			style.drawComplexControl(QtWidgets.QStyle.CC_Slider, opt, painter, self)

	def mousePressEvent(self, event):
		event.accept()

		style = QtWidgets.QApplication.style()
		button = event.button()

		# In a normal slider control, when the user clicks on a point in the
		# slider's total range, but not on the slider part of the control the
		# control would jump the slider value to where the user clicked.
		# For this control, clicks which are not direct hits will slide both
		# slider parts

		if button:
			opt = QtWidgets.QStyleOptionSlider()
			self.initStyleOption(opt)

			self.active_slider = -1

			for i, value in enumerate([self._low, self._high]):
				opt.sliderPosition = value
				hit = style.hitTestComplexControl(style.CC_Slider, opt, event.pos(), self)
				if hit == style.SC_SliderHandle:
					self.active_slider = i
					self.pressed_control = hit

					self.triggerAction(self.SliderMove)
					self.setRepeatAction(self.SliderNoAction)
					self.setSliderDown(True)
					break

			if self.active_slider < 0:
				self.pressed_control = QtWidgets.QStyle.SC_SliderHandle
				self.click_offset = self.__pixelPosToRangeValue(self.__pick(event.pos()))
				self.triggerAction(self.SliderMove)
				self.setRepeatAction(self.SliderNoAction)
		else:
			event.ignore()

	def mouseMoveEvent(self, event):
		if self.pressed_control != QtWidgets.QStyle.SC_SliderHandle:
			event.ignore()
			return

		event.accept()
		new_pos = self.__pixelPosToRangeValue(self.__pick(event.pos()))
		opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt)

		if self.active_slider < 0:
			offset = new_pos - self.click_offset
			self._high += offset
			self._low += offset
			if self._low < self.minimum():
				diff = self.minimum() - self._low
				self._low += diff
				self._high += diff
			if self._high > self.maximum():
				diff = self.maximum() - self._high
				self._low += diff
				self._high += diff
		elif self.active_slider == 0:
			if new_pos >= self._high:
				new_pos = self._high - 1
			self._low = new_pos
		else:
			if new_pos <= self._low:
				new_pos = self._low + 1
			self._high = new_pos

		self.click_offset = new_pos

		self.update()

		#self.emit(QtCore.SIGNAL('sliderMoved(int)'), new_pos)
		self.sliderMoved.emit(self._low, self._high)

	def __pick(self, pt):
		if self.orientation() == QtCore.Qt.Horizontal:
			return pt.x()
		else:
			return pt.y()


	def __pixelPosToRangeValue(self, pos):
		opt = QtWidgets.QStyleOptionSlider()
		self.initStyleOption(opt)
		style = QtWidgets.QApplication.style()

		gr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderGroove, self)
		sr = style.subControlRect(style.CC_Slider, opt, style.SC_SliderHandle, self)

		if self.orientation() == QtCore.Qt.Horizontal:
			slider_length = sr.width()
			slider_min = gr.x()
			slider_max = gr.right() - slider_length + 1
		else:
			slider_length = sr.height()
			slider_min = gr.y()
			slider_max = gr.bottom() - slider_length + 1

		return style.sliderValueFromPosition(self.minimum(), self.maximum(),
											 pos-slider_min, slider_max-slider_min,
											 opt.upsideDown)

class LabelledRangeSlider(QtWidgets.QWidget):
	def __init__(self, label, dflt_values:tuple, parent: QtWidgets.QWidget=None, label_bold=False, margins=[2,1,2,1]) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.values = [dflt_values[0], dflt_values[1]]
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout1.setSpacing(0)
		hlayout1.setContentsMargins(margins[0],margins[1],margins[2],margins[3])
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(margins[0],margins[1],margins[2],margins[3])
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(margins[0],margins[1],margins[2],margins[3])

		if label is not None:
			self._label_font = QtGui.QFont()
			if label_bold:
				self._label_font.setWeight(QtGui.QFont.Medium)
			self._label = QtWidgets.QLabel(label)
			self._label.setFont(self._label_font)
			hlayout1.addWidget(self._label)
		hlayout1.addStretch()
		vlayout.addLayout(hlayout1)

		self._range_slider = RangeSlider(QtCore.Qt.Orientation.Horizontal)
		self._range_slider.setMaximum(self.values[1])
		self._range_slider.setMinimum(self.values[0])
		self._range_slider.setHigh(self.values[1])
		self._range_slider.setLow(self.values[0])


		hlayout2.addWidget(self._range_slider)

		vlayout.addLayout(hlayout2)

		self.setLayout(vlayout)

	def setLow(self, val:int):
		self._range_slider.setLow(val)

	def setHigh(self, val:int):
		self._range_slider.setHigh(val)

	def getRange(self) -> tuple[int,int]:
		return self._range_slider.getRange()

class StretchTabWidget(QtWidgets.QTabWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.bar = StretchTabBar()
		self.setTabBar(self.bar)

	def resizeEvent(self, event):
		self.tabBar().setFixedWidth(self.width())
		super().resizeEvent(event)

class StretchTabBar(QtWidgets.QTabBar):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setExpanding(True)

	def tabSizeHint(self, index):
		if self.count() > 0:
			size = QtWidgets.QTabBar.tabSizeHint(self, index)
			if self.parent().tabPosition() in [QtWidgets.QTabWidget.West or QtWidgets.QTabWidget.East]:
				height = int(self.parent().size().height()/self.count())
				return QtCore.QSize(size.width(), height)
			elif self.parent().tabPosition() in [QtWidgets.QTabWidget.North or QtWidgets.QTabWidget.South]:
				width = int(self.parent().size().width()/self.count())
				return QtCore.QSize(width, size.height())
		return super().tabSizeHint(index)

class ColumnarStackedTabBar(QtWidgets.QTabBar):
	def __init__(self, parent=None):
		super().__init__(parent)

	def tabSizeHint(self, index):
		s = super().tabSizeHint(index)
		s.transpose()
		return s

	def paintEvent(self, event):
		painter = QtWidgets.QStylePainter(self)
		opt = QtWidgets.QStyleOptionTab()

		for i in range(self.count()):
			self.initStyleOption(opt, i)
			painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, opt)
			painter.save()

			s = opt.rect.size()
			s.transpose()
			r = QtCore.QRect(QtCore.QPoint(), s)
			r.moveCenter(opt.rect.center())
			opt.rect = r

			c = self.tabRect(i).center()
			painter.translate(c)
			painter.rotate(90)
			painter.translate(-c)
			painter.drawControl(QtWidgets.QStyle.CE_TabBarTabLabel, opt)
			painter.restore()

class ColumnarStackedTabWidget(QtWidgets.QTabWidget):
	tab_changed = QtCore.pyqtSignal(int,int)

	def __init__(self, *args, **kwargs):
		QtWidgets.QTabWidget.__init__(self, *args, **kwargs)
		self.setTabBar(ColumnarStackedTabBar())
		self.setTabPosition(QtWidgets.QTabWidget.West)
		self.curr_tab_idx = -1
		self.currentChanged.connect(self._onTabChange)

	def _onTabChange(self, new_idx):
		self.tab_changed.emit(self.curr_tab_idx, new_idx)
		self.curr_tab_idx = new_idx

class PrimaryConfigDisplay(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget|None=None):
		super().__init__(parent)

		self.pane_layout = QtWidgets.QVBoxLayout()
		# self.pane_layout = QtWidgets.QGridLayout()
		self._cnfg_label = QtWidgets.QLabel('Configuration Preview')

		self._cnfg_table = QtWidgets.QTableWidget(1,2)
		self._cnfg_table.setRowCount(2)
		self._cnfg_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self._cnfg_table.setItem(0,0,QtWidgets.QTableWidgetItem('Configuration File:'))
		self._cnfg_table.setItem(1,0,QtWidgets.QTableWidgetItem('Configuration Name:'))

		self._satellites_table = QtWidgets.QTableWidget(1,2)
		self._satellites_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self._satellites_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

		self._entry_font = self._cnfg_table.item(0,0).font()
		self._header_font = self._cnfg_table.item(0,0).font()
		self._entry_font.setPointSize(9)
		self._header_font.setPointSize(10)
		self._header_font.setWeight(QtGui.QFont.Medium)
		self._sensor_tables = []

		self._setStyling()

		self.pane_layout.addWidget(self._cnfg_label)
		self.pane_layout.addWidget(self._cnfg_table)
		self.pane_layout.addWidget(self._satellites_table)

		self.setLayout(self.pane_layout)

	def _setStyling(self):
		# Config title
		_label_font = QtGui.QFont()
		_label_font.setWeight(QtGui.QFont.Medium)
		self._cnfg_label.setFont(_label_font)
		self._cnfg_table.setStyleSheet('''
										QTableWidget {
														background-color:#00000000;
										}
									''');
		self._cnfg_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self._cnfg_table.setFocusPolicy(QtCore.Qt.NoFocus)
		self._cnfg_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		for row_num in range(self._cnfg_table.rowCount()):
			self._cnfg_table.setRowHeight(row_num, 6)
			for col_num in range(self._cnfg_table.columnCount()):
				if self._cnfg_table.item(row_num,col_num) is not None:
					if col_num == 0:
						self._cnfg_table.item(row_num,col_num).setFont(self._header_font)
					else:
						self._cnfg_table.item(row_num,col_num).setFont(self._entry_font)

		self._cnfg_table.verticalHeader().hide()
		self._cnfg_table.horizontalHeader().hide()
		self._cnfg_table.setShowGrid(False)
		self._cnfg_table.setFixedSize(self._cnfg_table.sizeHint())

		# Satelites table
		self._satellites_table.setHorizontalHeaderLabels(['Sat Name', 'Satcat ID'])
		self._satellites_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
		self._satellites_table.horizontalHeader().setFont(self._header_font)
		self._satellites_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self._satellites_table.setFocusPolicy(QtCore.Qt.NoFocus)
		self._satellites_table.verticalHeader().hide()
		for row_num in range(self._satellites_table.rowCount()):
			self._satellites_table.setRowHeight(row_num, 6)
			for col_num in range(self._satellites_table.columnCount()):
				if self._satellites_table.item(row_num,col_num) is not None:
					self._satellites_table.item(row_num,col_num).setFont(self._entry_font)

		self._satellites_table.horizontalHeader().setStyleSheet('''
														QHeaderView::section {
																background-color: #00000000;
    															border: 0px;
														}
														''')
		self._satellites_table.setStyleSheet('''
												QTableWidget {
																background-color:#00000000;
												}
											''');
		self._satellites_table.setShowGrid(False)
		self._satellites_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self._satellites_table.setFixedSize(self._satellites_table.sizeHint())

	def _setSensorTableStyling(self, table:QtWidgets.QTableWidget):

		table.setHorizontalHeaderLabels(['Sensor Suite', 'Sensor','',''])
		table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
		table.horizontalHeader().setFont(self._header_font)

		table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
		table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
		table.verticalHeader().hide()
		table.setStyleSheet('''
								QTableWidget {
											background-color:#00000000;
											}
							''');
		table.horizontalHeader().setStyleSheet('''
													QHeaderView::section {
																		background-color: #00000000;
    																	border: 0px;
																		}
												''')
		table.setShowGrid(False)

		# set row heights and fonts
		table_height = 0
		for row_num in range(table.rowCount()):
			table.setRowHeight(row_num, 6)
			table_height += table.rowHeight(row_num)
			for col_num in range(table.columnCount()):
				if table.item(row_num,col_num) is not None:
					table.item(row_num,col_num).setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
					table.item(row_num,col_num).setFont(self._entry_font)

		table.resizeColumnsToContents()

		# Turn off scrollbar
		table.verticalScrollBar().setDisabled(True)
		table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff);
		table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		table.setMinimumHeight(table.sizeHint().height());

	def updateConfig(self, config:satplot_data_types.PrimaryConfig):
		self.config = config
		self._cnfg_table.setItem(0,1,QtWidgets.QTableWidgetItem(f'{self.config.filestem}.json'))
		self._cnfg_table.setItem(1,1,QtWidgets.QTableWidgetItem(f'{self.config.name}'))
		self._cnfg_table.resizeColumnsToContents()
		self._populateSatellites()
		self._satellites_table.resizeColumnsToContents()
		self._setStyling()

	def clearConfig(self) -> None:
		self._satellites_table.setRowCount(0)

	def _populateSatellites(self):
		# delete old widgets
		for ii in range(len(self._sensor_tables)-1,-1,-1):
			if isinstance(self._sensor_tables[ii],QtWidgets.QSpacerItem):
				self.pane_layout.removeItem(self._sensor_tables[ii])
			else:
				self._sensor_tables[ii].deleteLater()
			# if isinstance(self._sensor_tables[ii],CollapsibleSection):
			# 	self.grid_row -= 1
			self._sensor_tables.pop(ii)


		num_sats = self.config.num_sats
		self._satellites_table.setRowCount(num_sats)
		# Populate list of satellites in primary config
		for ii, (sat_id, sat_name) in enumerate(self.config.sats.items()):
			self._satellites_table.setItem(ii, 0, QtWidgets.QTableWidgetItem(sat_name))
			self._satellites_table.setItem(ii, 1, QtWidgets.QTableWidgetItem(str(sat_id)))

		for sat_id, satellite in self.config.sat_configs.items():
			# For each satellite create collapsible section
			sat_cs = CollapsibleSection(title=satellite.name)
			# self.pane_layout.addWidget(sat_cs, self.grid_row,0)
			self.pane_layout.addWidget(sat_cs)
			# self.grid_row+=1
			self._sensor_tables.append(sat_cs)

			sat_cs.toggleCollapsed()

			if satellite.getNumSuites()==0:
				self.pane_layout.addWidget(QtWidgets.QLabel('No Sensors'))
			else:
				num_rows = 0
				# calculate how many rows to contain all data about sensor suites
				for suite_name, suite in satellite.sensor_suites.items():
					for sens_name in suite.getSensorNames():
						sens_config = suite.getSensorDisplayConfig(sens_name)
						num_rows += len(sens_config.keys())

				sat_table = QtWidgets.QTableWidget(num_rows,4)
				row_num = 0
				for suite_name, suite in satellite.sensor_suites.items():
					sat_table.setItem(row_num,0,QtWidgets.QTableWidgetItem(suite_name))
					for sens_name in suite.getSensorNames():
						sens_config = suite.getSensorDisplayConfig(sens_name)
						sat_table.setItem(row_num,1,QtWidgets.QTableWidgetItem(sens_name))
						# row_num += 1
						for field, val in sens_config.items():
							sat_table.setItem(row_num,2,QtWidgets.QTableWidgetItem(f'{field}:'))
							sat_table.setItem(row_num,3,QtWidgets.QTableWidgetItem(val))
							row_num += 1
						# add row between sensors
						row_num += 1

				self._setSensorTableStyling(sat_table)
				sat_cs.addWidget(sat_table)
				self._sensor_tables.append(sat_table)

class ConstellationConfigDisplay(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget|None=None):
		super().__init__(parent)

		self.pane_layout = QtWidgets.QVBoxLayout()
		# self.pane_layout = QtWidgets.QGridLayout()
		self._cnfg_label = QtWidgets.QLabel('Configuration Preview')

		self._cnfg_table = QtWidgets.QTableWidget(1,2)
		self._cnfg_table.setRowCount(2)
		self._cnfg_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self._cnfg_table.setItem(0,0,QtWidgets.QTableWidgetItem('Configuration File:'))
		self._cnfg_table.setItem(1,0,QtWidgets.QTableWidgetItem('Configuration Name:'))
		self._cnfg_table.setItem(2,0,QtWidgets.QTableWidgetItem('Configuration Beam Width:'))

		self._satellites_table = QtWidgets.QTableWidget(1,2)
		self._satellites_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
		self._satellites_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

		self._entry_font = self._cnfg_table.item(0,0).font()
		self._header_font = self._cnfg_table.item(0,0).font()
		self._entry_font.setPointSize(9)
		self._header_font.setPointSize(10)
		self._header_font.setWeight(QtGui.QFont.Medium)
		self._sensor_tables = []

		self._setStyling()

		self.pane_layout.addWidget(self._cnfg_label)
		self.pane_layout.addWidget(self._cnfg_table)
		self.pane_layout.addWidget(self._satellites_table)

		self.setLayout(self.pane_layout)

	def _setStyling(self):
		# Config title
		_label_font = QtGui.QFont()
		_label_font.setWeight(QtGui.QFont.Medium)
		self._cnfg_label.setFont(_label_font)
		self._cnfg_table.setStyleSheet('''
										QTableWidget {
														background-color:#00000000;
										}
									''');
		self._cnfg_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self._cnfg_table.setFocusPolicy(QtCore.Qt.NoFocus)
		self._cnfg_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		for row_num in range(self._cnfg_table.rowCount()):
			self._cnfg_table.setRowHeight(row_num, 6)
			for col_num in range(self._cnfg_table.columnCount()):
				if self._cnfg_table.item(row_num,col_num) is not None:
					if col_num == 0:
						self._cnfg_table.item(row_num,col_num).setFont(self._header_font)
					else:
						self._cnfg_table.item(row_num,col_num).setFont(self._entry_font)

		self._cnfg_table.verticalHeader().hide()
		self._cnfg_table.horizontalHeader().hide()
		self._cnfg_table.setShowGrid(False)
		self._cnfg_table.setFixedSize(self._cnfg_table.sizeHint())

		# Satelites table
		self._satellites_table.setHorizontalHeaderLabels(['Sat Name', 'Satcat ID'])
		self._satellites_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
		self._satellites_table.horizontalHeader().setFont(self._header_font)
		self._satellites_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		self._satellites_table.setFocusPolicy(QtCore.Qt.NoFocus)
		self._satellites_table.verticalHeader().hide()
		for row_num in range(self._satellites_table.rowCount()):
			self._satellites_table.setRowHeight(row_num, 6)
			for col_num in range(self._satellites_table.columnCount()):
				if self._satellites_table.item(row_num,col_num) is not None:
					self._satellites_table.item(row_num,col_num).setFont(self._entry_font)

		self._satellites_table.horizontalHeader().setStyleSheet('''
														QHeaderView::section {
																background-color: #00000000;
    															border: 0px;
														}
														''')
		self._satellites_table.setStyleSheet('''
												QTableWidget {
																background-color:#00000000;
												}
											''');
		self._satellites_table.setShowGrid(False)
		self._satellites_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self._satellites_table.setFixedSize(self._satellites_table.sizeHint())

	def updateConfig(self, config:satplot_data_types.ConstellationConfig):
		self.config = config
		self._cnfg_table.setItem(0,1,QtWidgets.QTableWidgetItem(f'{self.config.filestem}.json'))
		self._cnfg_table.setItem(1,1,QtWidgets.QTableWidgetItem(f'{self.config.name}'))
		self._cnfg_table.setItem(2,1,QtWidgets.QTableWidgetItem(f'{self.config.beam_width}'))
		self._cnfg_table.resizeColumnsToContents()
		self._populateSatellites()
		self._satellites_table.resizeColumnsToContents()
		self._setStyling()

	def clearConfig(self) -> None:
		self._satellites_table.setRowCount(0)

	def _populateSatellites(self):
		num_sats = self.config.num_sats
		self._satellites_table.setRowCount(num_sats)
		# Populate list of satellites in primary config
		for ii, (sat_id, sat_name) in enumerate(self.config.sats.items()):
			self._satellites_table.setItem(ii, 0, QtWidgets.QTableWidgetItem(sat_name))
			self._satellites_table.setItem(ii, 1, QtWidgets.QTableWidgetItem(str(sat_id)))

class MultiSelector(QtWidgets.QWidget):
	def __init__(self, left_label:str='', right_label:str='', left_list=[], right_list=[], parent: QtWidgets.QWidget|None=None):
		super().__init__(parent)

		pane_layout = QtWidgets.QHBoxLayout()
		left_vlayout = QtWidgets.QVBoxLayout()
		btn_layout = QtWidgets.QVBoxLayout()
		right_vlayout = QtWidgets.QVBoxLayout()

		_label_font = QtGui.QFont()
		_label_font.setWeight(QtGui.QFont.Medium)

		if left_label != '':
			_left_label = QtWidgets.QLabel(left_label)
			_left_label.setFont(_label_font)
			left_vlayout.addWidget(_left_label)

		if right_label != '':
			_right_label = QtWidgets.QLabel(right_label)
			_right_label.setFont(_label_font)
			right_vlayout.addWidget(_right_label)

		self.left_list = QtWidgets.QListWidget()
		self.left_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.right_list = QtWidgets.QListWidget()
		self.right_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

		self.move_right = QtWidgets.QPushButton()
		self.move_right.setIcon(QtGui.QIcon('resources/icons/arrow.png'))
		self.move_right.clicked.connect(self._transferToRight)

		self.move_left = QtWidgets.QPushButton()
		self.move_left.setIcon(QtGui.QIcon('resources/icons/arrow-180.png'))
		self.move_left.clicked.connect(self._transferToLeft)

		btn_layout.addStretch()
		btn_layout.addWidget(self.move_right)
		btn_layout.addWidget(self.move_left)
		btn_layout.addStretch()

		left_vlayout.addWidget(self.left_list)
		right_vlayout.addWidget(self.right_list)

		pane_layout.addLayout(left_vlayout)
		pane_layout.addLayout(btn_layout)
		pane_layout.addLayout(right_vlayout)

		self.setLayout(pane_layout)
		left_list.sort()
		right_list.sort()
		for el in left_list:
			self.left_list.addItem(QtWidgets.QListWidgetItem(el))

		for el in right_list:
			self.right_list.addItem(QtWidgets.QListWidgetItem(el))

	def _transferToRight(self):
		transfer_list = self.left_list.selectedItems()
		transfer_idx = [self.left_list.row(item) for item in transfer_list]
		for ii, item in enumerate(transfer_list):
			self.left_list.takeItem(transfer_idx[ii])
			self.right_list.addItem(item)

	def _transferToLeft(self):
		transfer_list = self.right_list.selectedItems()
		transfer_idx = [self.right_list.row(item) for item in transfer_list]
		for ii, item in enumerate(transfer_list):
			self.right_list.takeItem(transfer_idx[ii])
			self.left_list.addItem(item)

	def getRightEntries(self):
		vals = []
		for row_num in range(self.right_list.count()):
			item = self.right_list.item(row_num)
			vals.append(item.text())
		return vals

	def getLeftEntries(self):
		vals = []
		for row_num in range(self.left_list.count()):
			item = self.left_list.item(row_num)
			vals.append(item.text())
		return vals

def embedWidgetsInHBoxLayout(w_list, margin=5):
	"""Embed a list of widgets into a layout to give it a frame"""
	result = QtWidgets.QWidget()
	layout = QtWidgets.QHBoxLayout(result)
	layout.setContentsMargins(margin, margin, margin, margin)
	if isinstance(w_list, list):
		for w in w_list:
			layout.addWidget(w)
	else:
		layout.addWidget(w_list)
	return result

def embedWidgetsInVBoxLayout(w_list, margin=5):
	"""Embed a list of widgets into a layout to give it a frame"""
	result = QtWidgets.QWidget()
	layout = QtWidgets.QVBoxLayout(result)
	layout.setContentsMargins(margin, margin, margin, margin)
	if isinstance(w_list, list):
		for w in w_list:
			layout.addWidget(w)
	else:
		layout.addWidget(w_list)
	return result