from PyQt5 import QtWidgets, QtCore
import math
import satplot.visualiser.colours as colours
import datetime as dt
import satplot.visualiser.controls.console as console

class TimeSlider(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)

		self.range = 2*math.pi
		self.num_ticks = 1440
		self.range_per_tick = self.range/self.num_ticks
		self._callbacks = []
		layout = QtWidgets.QVBoxLayout()
		self.label = QtWidgets.QLabel("Rotation")
		self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
		self.slider.setMinimum(0)
		self.slider.setMaximum(self.num_ticks)
		self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
		self.slider.setTickInterval(1)
		layout.addWidget(self.label)
		layout.addWidget(self.slider)
		self.slider.valueChanged.connect(self._run_callbacks)
		self.setLayout(layout)
		layout.addStretch(1)
		self.setLayout(layout)

	def setTicks(self, num_ticks):
		self.num_ticks = num_ticks
		self.slider.setMaximum(self.num_ticks-1)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.slider.value())
		else:
			print("No Time Slider callbacks are set")

class ColourPicker(QtWidgets.QWidget):
	def __init__(self, label, dflt_col, parent: QtWidgets.QWidget=None) -> None:
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
		self._colorpicker.currentColorChanged.connect(self._run_callbacks)
		self._text_box.returnPressed.connect(self._run_callbacks)
		
		self.setLayout(closed_layout)

	def add_connect(self, callback):
		self._callbacks.append(callback)

	def _run_callbacks(self):
		rgb_str = self._text_box.text().split(',')
		self.curr_rgb = (int(rgb_str[0]), int(rgb_str[1]), int(rgb_str[2]))
		self.curr_hex = colours.rgb2hex(self.curr_rgb)
		self._colour_box.setStyleSheet(f"background-color: {self.curr_hex}")
		# self._colour_box.setStyleSheet(f"onClicked: forceActiveFocus()")
		print(self._colour_box.styleSheet())
		if len(self._callbacks) > 0:
			for callback in self._callbacks:
				callback(self.curr_rgb)
		else:
			print("No Colour Picker callbacks are set")

class ToggleBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_state, parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.curr_state = dflt_state
		layout = QtWidgets.QHBoxLayout()
		layout.setSpacing(0)
		layout.setContentsMargins(2,1,2,1)

		self._label = QtWidgets.QLabel(label)
		self._checkbox = QtWidgets.QCheckBox()
		self._checkbox.setChecked(dflt_state)
		layout.addWidget(self._label)
		layout.addStretch()
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

class OptionBox(QtWidgets.QWidget):
	def __init__(self, label, dflt_state=None, options_list=[], parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self._curr_index = []
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

		self._label = QtWidgets.QLabel(label)
		self._optionbox = QtWidgets.QComboBox()
		for item in options_list:
			self._optionbox.addItem(item)

		hlayout1.addWidget(self._label)
		hlayout1.addStretch()
		hlayout2.addWidget(self._optionbox)
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

		self._optionbox.currentIndexChanged.connect((self._run_callbacks))

	def currentIndex(self):
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

class FilePicker(QtWidgets.QWidget):
	def __init__(self, label, dflt_file='', parent: QtWidgets.QWidget=None) -> None:
		super().__init__(parent)
		self._callbacks = []
		self.path = dflt_file
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout2 = QtWidgets.QHBoxLayout()
		vlayout.setSpacing(0)
		hlayout1.setSpacing(0)
		hlayout2.setSpacing(0)
		hlayout1.setContentsMargins(0,1,0,1)
		hlayout2.setContentsMargins(0,1,10,1)

		self._label = QtWidgets.QLabel(label)
		self._file_text_box = QtWidgets.QLineEdit(self.path)
		self._dialog_button = QtWidgets.QPushButton('...')
		self._dialog_button.clicked.connect(self.openFilenameDialog)
		self._dialog_button.setFixedWidth(25)


		hlayout1.addWidget(self._label)
		hlayout1.addStretch()
		hlayout2.addWidget(self._file_text_box)
		hlayout2.addSpacing(5)
		hlayout2.addWidget(self._dialog_button)
		vlayout.addLayout(hlayout1)
		vlayout.addLayout(hlayout2)
		self.setLayout(vlayout)

	def openFilenameDialog(self):
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
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
		
		self._label = QtWidgets.QLabel(label)
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

		hlayout1.addWidget(self._label)
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
		self.datetime = dt.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
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

class CollapsibleSection(QtWidgets.QWidget):
# Ported to PyQT5 and modified, original widget by Caroline Beyne, github user: cbeyne
# https://github.com/By0ute/pyqt-collapsible-widget/blob/master/code/FrameLayout.py
	def __init__(self, parent=None, title=None):
		QtWidgets.QFrame.__init__(self, parent=parent)

		self._is_collasped = True
		self._title_frame = None
		self._content, self._content_layout = (None, None)

		self.v_layout = QtWidgets.QVBoxLayout(self)
		self.v_layout.addWidget(self.initTitleFrame(title, self._is_collasped))
		self.v_layout.addWidget(self.initContent(self._is_collasped))
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
		self._content.setVisible(self._is_collasped)
		self._content_layout.setAlignment(QtCore.Qt.AlignLeft)
		self.v_layout.setAlignment(QtCore.Qt.AlignLeft)
		self._is_collasped = not self._is_collasped

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