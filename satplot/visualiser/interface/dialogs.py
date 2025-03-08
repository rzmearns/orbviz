import datetime as dt
import pickle
import os

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import satplot
import satplot.util.paths as paths
import satplot.visualiser.interface.widgets as widgets

def createSpaceTrackCredentialsDialog():
	SpaceTrackCredentialsDialog()

class SpaceTrackCredentialsDialog():
	def __init__(self):
		self.window = QtWidgets.QDialog()
		self.window.setWindowTitle('SpaceTrack Credentials')
		label = QtWidgets.QLabel('Please enter your credentials below')
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(label)

		layout.addWidget(QtWidgets.QLabel('Username:'))
		self.user = QtWidgets.QLineEdit('')
		layout.addWidget(self.user)
		layout.addWidget(QtWidgets.QLabel('Password:'))
		layout.addStretch()
		self.passwd = QtWidgets.QLineEdit('')
		self.passwd.setEchoMode(QtWidgets.QLineEdit.Password)
		layout.addWidget(self.passwd)

		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout1.addStretch()
		hlayout1.addWidget(QtWidgets.QLabel('Save Credentials Locally'))			
		self.save_locally = QtWidgets.QCheckBox()
		hlayout1.addWidget(self.save_locally)
		layout.addLayout(hlayout1)
		layout.addWidget(QtWidgets.QLabel('<i>If credentials are not saved locally,<br>they will have to be entered every<br>time<\i>'))


		hlayout2 = QtWidgets.QHBoxLayout()
		okbutton = QtWidgets.QPushButton('Submit')
		cancelbutton = QtWidgets.QPushButton('Cancel')
		hlayout2.addWidget(okbutton)
		hlayout2.addStretch()
		hlayout2.addWidget(cancelbutton)
		
		layout.addLayout(hlayout2)

		self.window.setLayout(layout)


		okbutton.clicked.connect(self.submit)
		cancelbutton.clicked.connect(self.cancel)

		# Show the dialog as a modal dialog (blocks the main window)
		self.window.exec_()

	def submit(self):
		credential_file = 'data/spacetrack/.credentials'
		self.window.close()
		satplot.spacetrack_credentials['user'] = self.user.text()
		satplot.spacetrack_credentials['passwd'] = self.passwd.text()
		if self.save_locally.isChecked():
			with open(credential_file,'wb') as fp:
				pickle.dump(satplot.spacetrack_credentials,fp)		
		else:
			try:
				os.remove(credential_file)
			except FileNotFoundError:
				pass

	def cancel(self):
		self.window.close()


class GIFDialog():
	def __init__(self, parent_window, opening_context, camera_type:str, dflt_camera_data:dict[str,float], num_ticks:int):

		if camera_type not in ['Turntable']:
			raise ValueError("GIF capture not supported for this context's camera type")

		self.parent = parent_window
		self.opening_context = opening_context
		self.window = QtWidgets.QDialog(parent=self.parent)
		self.name_str = ' '.join(self.opening_context.config['name'].split('_')).capitalize()
		self.fname_str = self.opening_context.config['name']
		self.window.setWindowTitle(f'Save {self.name_str} GIF')
		self.window.setWindowModality(QtCore.Qt.NonModal)

		self._loop_option = widgets.ToggleBox("Loop GIF?", True)
		self._file_selector = widgets.FilePicker("Save GIF as:",
										   			dflt_file=f"{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{self.fname_str}.gif",
													dflt_dir=f'{paths.data_dir}/gifs/',
													save=True,
													margins=[0,0,0,0],
													width=600)
		self.min_size = None

		store_start = QtWidgets.QPushButton('Store Start Time')
		store_start.clicked.connect(self.storeStartTime)
		store_start.setToolTip("Use Main Window's current displayed time as the GIF start time")
		store_end = QtWidgets.QPushButton('Store End Time')
		store_end.clicked.connect(self.storeEndTime)
		store_end.setToolTip("Use Main Window's current displayed time as the GIF end time")

		# start_time_display = widgets.SmallDatetimeEntry()
		# end_time_display =

		self._time_slider = widgets.LabelledRangeSlider('Timespan to capture:',(0,num_ticks))

		self._camera_adjust_option = widgets.ToggleBox("Adjust camera while capturing?", False)

		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self._file_selector)

		hlayout1 = QtWidgets.QHBoxLayout()
		hlayout1.addWidget(self._loop_option)
		hlayout1.addStretch()
		layout.addLayout(hlayout1)

		hlayout2 = QtWidgets.QHBoxLayout()
		hlayout2.addWidget(self._camera_adjust_option)
		hlayout2.addStretch()
		layout.addLayout(hlayout2)

		camera_adjust_hlayout = QtWidgets.QHBoxLayout()
		camera_adjust_vlayout = QtWidgets.QVBoxLayout()

		self._camera_adjust_extensions_options = QtWidgets.QWidget()
		self._camera_adjust_enable_list = []
		self._camera_adjust_option.add_connect(self._enableCameraAdjustState)
		self._camera_adjust_option.setState(False)
		self._enableCameraAdjustState(False)
		self._camera_adjust_option.add_connect(self._camera_adjust_extensions_options.setVisible)
		self.camera_adjustment_data_sources = {}

		if camera_type == 'Turntable':
			self._camera_adjust_option.setLabel("Rotate while capturing?")
			self._start_azimuth = widgets.ValueBox('Start Azimuth:', dflt_camera_data['az_start'], margins=[20,1,2,1])
			self._start_elevation = widgets.ValueBox('Start Elevation:', dflt_camera_data['el_start'], margins=[20,1,2,1])
			self._total_elevation_delta = widgets.ValueBox('Rotate Elevation Through:', 0, margins=[20,1,2,1])
			self._total_azimuth_delta = widgets.ValueBox('Rotate Azimuth Through:', 360, margins=[20,1,2,1])
			self.camera_adjustment_data_sources['az_start'] = self._start_azimuth
			self.camera_adjustment_data_sources['el_start'] = self._start_elevation
			self.camera_adjustment_data_sources['az_range'] = self._total_azimuth_delta
			self.camera_adjustment_data_sources['el_range'] = self._total_elevation_delta
			self._addWidgetToCameraAdjustEnabled(self._start_azimuth)
			self._addWidgetToCameraAdjustEnabled(self._start_elevation)
			self._addWidgetToCameraAdjustEnabled(self._total_azimuth_delta)
			self._addWidgetToCameraAdjustEnabled(self._total_elevation_delta)
			camera_adjust_vlayout.addWidget(self._start_azimuth)
			camera_adjust_vlayout.addWidget(self._start_elevation)
			camera_adjust_vlayout.addWidget(self._total_elevation_delta)
			camera_adjust_vlayout.addWidget(self._total_azimuth_delta)

		camera_adjust_hlayout.addLayout(camera_adjust_vlayout)
		camera_adjust_hlayout.addStretch()
		self._camera_adjust_extensions_options.setLayout(camera_adjust_hlayout)
		self._camera_adjust_extensions_options.setVisible(False)

		layout.addWidget(self._camera_adjust_extensions_options)
		layout.addWidget(self._time_slider)

		hlayout4 = QtWidgets.QHBoxLayout()
		hlayout4.addWidget(store_start)
		hlayout4.addStretch()
		hlayout4.addWidget(store_end)
		layout.addLayout(hlayout4)

		hlayout5 = QtWidgets.QHBoxLayout()
		hlayout5.addWidget(store_start)
		hlayout5.addStretch()
		hlayout5.addWidget(store_end)
		layout.addLayout(hlayout5)

		butt_hlayout = QtWidgets.QHBoxLayout()
		okbutton = QtWidgets.QPushButton('Submit')
		cancelbutton = QtWidgets.QPushButton('Cancel')
		butt_hlayout.addWidget(okbutton)
		butt_hlayout.addStretch()
		butt_hlayout.addWidget(cancelbutton)
		layout.addLayout(butt_hlayout)

		okbutton.clicked.connect(self.submit)
		cancelbutton.clicked.connect(self.cancel)

		layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
		self.window.setLayout(layout)

		self.min_size = self.window.size()

		self.window.show()

	def _isCameraAdjustEnabled(self) -> bool:
		return self._camera_adjust_option.getState()

	def _addWidgetToCameraAdjustEnabled(self, widget:QtWidgets.QWidget) -> None:
		self._camera_adjust_enable_list.append(widget)

	def _enableCameraAdjustState(self, state:bool) -> None:
		for widget in self._camera_adjust_enable_list:
			widget.setDisabled(not state)
		if not state and self.min_size is not None:
			self.window.adjustSize()
			self.window.resize(self.min_size)

	def storeStartTime(self):
		low = self.opening_context.controls.getCurrIndex()
		self._time_slider.setLow(low)

	def storeEndTime(self):
		high = self.opening_context.controls.getCurrIndex()
		self._time_slider.setHigh(high)

	def cancel(self):
		self.window.close()

	def submit(self):
		self.window.close()
		slider_range = self._time_slider.getRange()
		camera_adjustment_data = {}
		if self._isCameraAdjustEnabled():

			for k,v in self.camera_adjustment_data_sources.items():
				camera_adjustment_data[k] = v.getValue()

			self.opening_context.saveGif(self._file_selector.getPath(),
										loop=self._loop_option.getState(),
										camera_adjustment_data=camera_adjustment_data,
										start_index=slider_range[0],
										end_index=slider_range[1])
		else:
			for k,v in self.camera_adjustment_data_sources.items():
				camera_adjustment_data[k] = v.getValue()
				if 'range' in k:
					camera_adjustment_data[k] = 0

			self.opening_context.saveGif(self._file_selector.getPath(),
										loop=self._loop_option.getState(),
										camera_adjustment_data=camera_adjustment_data,
										start_index=slider_range[0],
										end_index=slider_range[1])