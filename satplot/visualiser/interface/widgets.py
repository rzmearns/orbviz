import datetime as dt
import math
import pathlib
from typing import Any

from PyQt5 import QtWidgets, QtCore, QtGui

import satplot.visualiser.colours as colours


class TimeSlider(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self.start_dt = None
		self.end_dt = None
		self.range = 2*math.pi
		self.range_delta = None
		self.num_ticks = 1440
		self.range_per_tick = self.range/self.num_ticks
		self._callbacks = []
		vlayout = QtWidgets.QVBoxLayout()
		vlayout.setSpacing(0)
		vlayout.setContentsMargins(2,1,2,1)
		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout2.setSpacing(0)
		hlayout2.setContentsMargins(2,1,2,1)
		hlayout3 = QtWidgets.QHBoxLayout()
		hlayout3.setSpacing(0)
		hlayout3.setContentsMargins(2,1,2,1)
		self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
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

	def setRange(self, start_dt, end_dt, num_ticks):
		if start_dt > end_dt:
			raise ValueError(f"Period End {end_dt} must be after Period Start {start_dt}")
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
			prev_index = int(((datetime-self.start_dt)/self.tick_delta))
		curr_datetime = self.start_dt + (prev_index*self.tick_delta)
		self._curr_dt_picker.setDatetime(curr_datetime)
		self.slider.setValue(prev_index)

	def getDatetime(self) -> dt.datetime:
		return self.curr_datetime

	def setTicks(self, num_ticks):
		self.num_ticks = num_ticks
		self.slider.setMaximum(self.num_ticks-1)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		self._curr_dt_picker.setDatetime(self.start_dt + (self.slider.value()*self.tick_delta))
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.slider.value())
		else:
			print("No Time Slider callbacks are set")

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
			print(f"{self} state was serialised as a {state['type']}, is now a timeSlider")
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
		print(self._colour_box.styleSheet())
		# self._colour_box.setStyleSheet(f"onClicked: forceActiveFocus()")
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.curr_rgb)
		else:
			print("No Colour Picker callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ColourPicker'
		state['value'] = self.curr_rgb
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ColourPicker':
			print(f"{self} state was serialised as a {state['type']}, is now a ColourPicker")

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
			print("No Value Spinner callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ValueSpinner'
		state['value'] = self.curr_val
		state['allow_float'] = self.allow_float
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ValueSpinner':
			print(f"{self} state was serialised as a {state['type']}, is now a ValueSpinner")

		self._val_box.blockSignals(True)
		self.curr_val = state['value']
		if self.allow_float:
			self._val_box.setValue(float(self.curr_val))
		else:
			self._val_box.setValue(int(self.curr_val))
		self._val_box.blockSignals(False)

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
		self._checkbox.stateChanged.connect((self._run_callbacks))

		self.setLayout(layout)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self._checkbox.isChecked())
		else:
			print("No Toggle Box callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ToggleBox'
		state['value'] = self._checkbox.isChecked()
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ToggleBox':
			print(f"{self} state was serialised as a {state['type']}, is now a ToggleBox")
		self._checkbox.blockSignals(True)
		self._checkbox.setChecked(state['value'])
		a = QtWidgets.QCheckBox()
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
			vlayout.addLayout(hlayout1)

		self._optionbox = NonScrollingComboBox()
		for item in options_list:
			self._optionbox.addItem(item)
		self._optionbox.setFocusPolicy(QtCore.Qt.StrongFocus)
		hlayout1.addWidget(self._label)
		hlayout1.addStretch()
		hlayout2.addWidget(self._optionbox)
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

		self._optionbox.currentIndexChanged.connect(self._run_callbacks)
		self._optionbox.currentIndexChanged.connect(self.setCurrentIndex)

	def setCurrentIndex(self, idx:int) -> None:
		print(f'{idx}')
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
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(index)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'OptionBox'
		curr_idx = self.getCurrentIndex()+1
		if curr_idx is None:
			state['value'] = None
		else:
			state['value'] = self._optionbox.getAllItems()[curr_idx]
		print(f"{state['value']=}")
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'OptionBox':
			print(f"{self} state was serialised as a {state['type']}, is now an OptionBox")
			return
		if state['value'] is not None and state['value'] in self._optionbox.getAllItems():
			print(f"{state['value']=}")
			self._optionbox.setCurrentText(state['value'])
		else:
			print(f"{state['value']} is not a local valid option. Displaying data, but can't set options.", file=sys.stderr)

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
		self.path = f'{dflt_dir}{dflt_file}'
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		vlayout.setSpacing(0)
		hlayout1.setSpacing(0)
		hlayout2.setSpacing(0)
		hlayout1.setContentsMargins(0,1,0,0)
		hlayout2.setContentsMargins(0,0,10,1)
		vlayout.setContentsMargins(margins[0],margins[1],margins[2],margins[3])

		if label is not None:
			self._label = QtWidgets.QLabel(label)
			hlayout1.addWidget(self._label)
			hlayout1.addStretch()
			vlayout.addLayout(hlayout1)

		self._file_text_box = QtWidgets.QLineEdit(self.path)
		if width is not None:
			self._file_text_box.setFixedWidth(width)
		self._dialog_button = QtWidgets.QPushButton('...')
		self.caption = f'Pick {label}'
		self.dflt_dir = dflt_dir
		self.dflt_filename = dflt_file
		self.dialog_save = save
		self._dialog_button.clicked.connect(self.openFilenameDialog)
		self._file_text_box.textChanged.connect(self.setPath)
		self._dialog_button.setFixedWidth(25)


		hlayout2.addWidget(self._file_text_box)
		hlayout2.addSpacing(5)
		hlayout2.addWidget(self._dialog_button)

		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

	def setPath(self):
		self.path = self._file_text_box.text()

	def getPath(self) -> pathlib.Path:
		return pathlib.Path(self._file_text_box.text())

	def openFilenameDialog(self):
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		if self.dialog_save:
			filename, _ = QtWidgets.QFileDialog.getSaveFileName(self,
																self.caption,
																f'{self.dflt_dir}{self.dflt_filename}',
																"All Files (*)",
																options=options)
		else:
			filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,
																self.caption,
																f'{self.dflt_dir}{self.dflt_filename}',
																"All Files (*)",
																options=options)
			print(filename)
		self.path = filename
		self._file_text_box.setText(self.path)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self._checkbox.isChecked())
		else:
			print("No FilePicker callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'filePicker'
		state['value'] = self.path
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'filePicker':
			print(f"{self} state was serialised as a {state['type']}, is now a filePicker")
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
		S = int((self.period-H*3600-M*60))

		return H,M,S

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'period'
		state['value'] = self.period
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'period':
			print(f"{self} state was serialised as a {state['type']}, is now a period")
			return
		self.val_box.setValue(state['value'])

class DatetimeEntry(QtWidgets.QWidget):
	def __init__(self, label, dflt_datetime, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.datetime = dflt_datetime
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

		self._curr_dt = QtWidgets.QLabel(self.datetime.strftime("%Y-%m-%d   %H:%M:%S"))
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
		except ValueError:
			self.setDatetime(self.datetime)
			return
		self.datetime = dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
		self._curr_dt.setText(self.datetime.strftime("%Y-%m-%d   %H:%M:%S"))

	def setDatetime(self, datetime):
		self.datetime = datetime
		self._yr_text_box.setText(datetime.strftime("%Y"))
		self._mon_text_box.setText(datetime.strftime("%m"))
		self._day_text_box.setText(datetime.strftime("%d"))
		self._hr_text_box.setText(datetime.strftime("%H"))
		self._min_text_box.setText(datetime.strftime("%M"))
		self._sec_text_box.setText(datetime.strftime("%S"))
		self._curr_dt.setText(self.datetime.strftime("%Y-%m-%d   %H:%M:%S"))

	def addConnect(self, callback):
		self._callbacks.append(callback)

	def _runCallbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				pass
				# callback(self._checkbox.isChecked())
		else:
			print("No Toggle Box callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'DatetimeEntry'
		state['value'] = self.datetime
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'DatetimeEntry':
			print(f"{self} state was serialised as a {state['type']}, is now a DatetimeEntry")
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
		try:
			ret_val = float(self.value)
			return float(self.value)
		except:
			print(f"Can't return non float value")
			return ''

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
			print("No ValueBox callbacks are set")

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['type'] = 'ValueBox'
		state['value'] = str(self.value)
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['type'] != 'ValueBox':
			print(f"{self} state was serialised as a {state['type']}, is now a ValueBox")
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
			self._content_layout.setAlignment(QtCore.Qt.AlignLeft)
			self.v_layout.setAlignment(QtCore.Qt.AlignLeft)

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

class Switch(QtWidgets.QPushButton):
	toggle = QtCore.pyqtSignal(bool)
	def __init__(self, parent = None):
		super().__init__(parent)
		self.setCheckable(True)
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
			print(f"{self} state was serialised as a {state['type']}, is now a Switch")
			return
		self.setChecked(state['value'])

class NonScrollingComboBox(QtWidgets.QComboBox):
	def __init__(self, scrollWidget=None, *args, **kwargs):
		super(NonScrollingComboBox, self).__init__(*args, **kwargs)
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
		super(RangeSlider, self).__init__(*args)

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

		self._range_slider = RangeSlider(QtCore.Qt.Horizontal)
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