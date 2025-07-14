import datetime as dt
import pickle
import json
import numpy as np
import os
import pathlib
import pickle
from PIL import Image
import time

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5 import QtCore, QtGui
from vispy import scene
from vispy.app.canvas import MouseEvent

import satplot
from satplot.model.data_models import datapane as datapane_model
import satplot.util.hashing as satplot_hashing
import satplot.util.paths as satplot_paths
import satplot.visualiser.assets.widgets as vispy_widgets
import satplot.visualiser.cameras.RestrictedPanZoom as RestrictedPanZoom
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.datapane as datapane
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
	def __init__(self, parent_window, opening_context, camera_type:str, dflt_camera_data:dict[str,float], num_ticks:int, three_dim=True):
		if camera_type not in ['Turntable', 'RestrictedPanZoom']:
			raise ValueError("GIF capture not supported for this context's camera type")

		self.parent = parent_window
		self.opening_context = opening_context
		self.three_dim = three_dim
		self.window = QtWidgets.QDialog(parent=self.parent)
		self.name_str = ' '.join(self.opening_context.config['name'].split('_')).capitalize()
		self.fname_str = self.opening_context.config['name']
		self.window.setWindowTitle(f'Save {self.name_str} GIF')
		self.window.setWindowModality(QtCore.Qt.NonModal)

		self._loop_option = widgets.ToggleBox("Loop GIF?", True)
		print(f'{satplot_paths.data_dir=}')
		print(f'{satplot_paths.gifs_dir=}')
		self._file_selector = widgets.FilePicker("Save GIF as:",
										   			dflt_file=f"{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{self.fname_str}.gif",
													dflt_dir=f'{satplot_paths.gifs_dir}',
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

		if self.three_dim:
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

		if self.three_dim and self._isCameraAdjustEnabled() :

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

class fullResSensorImageDialog():
	create_time = time.monotonic()
	MIN_MOVE_UPDATE_THRESHOLD = 1
	MOUSEOVER_DIST_THRESHOLD = 5
	last_mevnt_time = time.monotonic()
	mouse_over_is_highlighting = False
	def __init__(self, img_data, mo_data, moConverterFunction, img_metadata):
		sc_name = img_metadata['spacecraft name']
		sens_suite_name = img_metadata['sensor suite name']
		sens_name = img_metadata['sensor name']
		width = img_metadata['resolution'][0]
		height = img_metadata['resolution'][1]
		datetime = img_metadata['current time [yyyy-mm-dd hh:mm:ss]']
		img_metadata['current time [yyyy-mm-dd hh:mm:ss]'] = datetime.strftime('%Y-%m-%d %H:%M:%S')

		self.filename = f"{sc_name}-{sens_suite_name}-{sens_name}-{datetime.strftime('%Y%m%d-%H%M%S')}.bmp"
		self.window = QtWidgets.QDialog()
		self.window.setWindowTitle(f'Sensor Image - {sc_name}:{sens_suite_name} - {sens_name}')
		vlayout = QtWidgets.QVBoxLayout()
		hlayout1 = QtWidgets.QHBoxLayout()
		self.canvas = scene.canvas.SceneCanvas(size=(width/2,height/2),
								keys='interactive',
								bgcolor='white',
								show=True)
		self.canvas.events.mouse_move.connect(self.onMouseMove)
		self.view = self.canvas.central_widget.add_view()
		self.view.camera = RestrictedPanZoom.RestrictedPanZoomCamera(limits=(0, width, 0, height))
		self.view.camera.aspect = 1
		self.view.camera.flip = (0,1,0)
		self.view.camera.set_range(x=(0,width),y=(0,height), margin=0)

		self.visuals={}
		self.img_data = img_data
		self.img_metadata = img_metadata
		self.visuals['image'] = scene.visuals.Image(
			img_data,
			parent=self.view.scene,
		)
		self.mo_data = mo_data
		self.moConverterFunction = moConverterFunction
		self.mouseOverText = vispy_widgets.PopUpTextBox(v_parent=self.canvas.scene,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)
		self.mouseOverTimer = QtCore.QTimer()
		# TODO: mouseover box doesn't show text in this dialog, somekind of bug,
		# Rely on datapane instead
		# self.mouseOverTimer.timeout.connect(self._setMouseOverVisible)
		self.mouseOverObject = None
		self.datapane_model = datapane_model.DataPaneModel()
		self.datapane = datapane.DataPaneWidget(self.datapane_model)

		datapane_hsplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
		datapane_hsplitter.setObjectName('window_hsplitter')
		datapane_hsplitter.setStyleSheet('''
					QSplitter#window_hsplitter::handle {
								background-color: #DCDCDC;
								padding: 2px;
							}
					QSplitter#window_hsplitter::handle:horizontal {
								height: 1px;
								color: #ff0000;
							}
							''')

		# hlayout1.addStretch()
		# hlayout1.addWidget(self.canvas.native)
		# hlayout1.addStretch()
		datapane_hsplitter.addWidget(self.canvas.native)
		datapane_hsplitter.addWidget(self.datapane)
		vlayout.addWidget(datapane_hsplitter)
		# vlayout.addLayout(hlayout1)

		hlayout2 = QtWidgets.QHBoxLayout()
		save_button = QtWidgets.QPushButton('Save')
		cancel_button = QtWidgets.QPushButton('Cancel')
		hlayout2.addStretch()
		hlayout2.addWidget(save_button)
		hlayout2.addStretch()
		hlayout2.addWidget(cancel_button)
		hlayout2.addStretch()

		vlayout.addLayout(hlayout2)

		save_button.clicked.connect(self.save)
		cancel_button.clicked.connect(self.cancel)
		self.mouseOverText.notifier.text_updated.connect(self.datapane.setMouseText)

		# Build Data Pane
		self._buildDataPane(img_metadata)

		# Show the dialog as a modal dialog (blocks the main window)
		self.window.setLayout(vlayout)
		self.window.exec_()

	def save(self):
		dflt_path = satplot_paths.screenshot_dir
		save_file = self._saveFileDialog('Sensor Image Save...', dflt_path, self.filename)
		if save_file.name != '':
			self.save_file = pathlib.Path(save_file)
			int_img_data = (self.img_data*255).astype(np.uint8)
			im = Image.fromarray(int_img_data)
			im.save(self.save_file)

			self.img_metadata['image md5 hash'] = satplot_hashing.md5(self.save_file)
			metadata_file = self.save_file.with_suffix('.md')
			with open(metadata_file,'w') as fp:
				json.dump(self.img_metadata,fp,indent=4)
			console.send(f'Saved sensor image as {save_file}')
			console.send(f'Saved sensor image metadata as {metadata_file}')

	def cancel(self):
		self.window.close()

	def _setMouseOverVisible(self):
		self.mouseOverText.setParent(self.view.scene)
		self.mouseOverText.setVisible(True)
		self.mouseOverText.setParent(self.canvas.scene)
		print(self.mouseOverText.text)
		self.mouseOverTimer.stop()

	def stopMouseOverTimer(self) -> None:
		self.mouseOverTimer.stop()

	def _mapCanvasPosToFractionalPos(self, canvas_pos:list[int]):
		vb_pos = (canvas_pos[0])/self.canvas.native.width(), canvas_pos[1]/self.canvas.native.height()
		return vb_pos

	def _buildDataPane(self, img_metadata):
		print('Building Img datapane')
		old_np_options = np.get_printoptions()
		np.set_printoptions(precision=4)
		for k,v in img_metadata.items():
			if '[' in k:
				param_str = k.split('[')[0]
				unit_str = f"[{'['.join(k.split('[')[1:])}"
			else:
				param_str = k
				unit_str = ''
			item = {'parameter':param_str,
					'value':v,
					'unit':unit_str}
			self.datapane_model.appendData(item)
			# self.shell_dict['history'].history_data_model.data_ready
		self.datapane_model.refresh()
		np.set_printoptions(**old_np_options)

	def onMouseMove(self, event:MouseEvent) -> None:
		global last_mevnt_time
		global mouse_over_is_highlighting

		# throttle mouse events to 50ms
		if time.monotonic() - self.last_mevnt_time < 0.05:
			return

		# reset mouseOver
		self.mouseOverTimer.stop()

		pp = event.pos
		vb_pos = self._mapCanvasPosToFractionalPos(pp)
		s = self.moConverterFunction(self.mo_data, vb_pos)

		self.mouseOverText.setText(s)
		self.mouseOverText.setAnchorPosWithinCanvas(pp, self.canvas)
		self.mouseOverTimer.start(300)
		self.mouseOverText.setVisible(False)

		last_mevnt_time = time.monotonic()
		pass

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		pass

	def _saveFileDialog(self, caption: str, dir:pathlib.Path, dflt_filename:str|None) -> pathlib.Path:
		if dflt_filename is None:
			dflt_filename = ''
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		filename, _ = QtWidgets.QFileDialog.getSaveFileName(None,
															caption,
															f'{dir}/{dflt_filename}',
															options=options)
		return pathlib.Path(filename)
