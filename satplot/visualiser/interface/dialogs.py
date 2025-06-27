import json
import numpy as np
import os
import pathlib
import pickle
from PIL import Image
import time

import PyQt5.QtWidgets as QtWidgets
from PyQt5 import QtCore, QtGui
from vispy import scene
from vispy.app.canvas import MouseEvent

import satplot
import satplot.util.hashing as satplot_hashing
import satplot.util.paths as satplot_paths
import satplot.visualiser.cameras.RestrictedPanZoom as RestrictedPanZoom
import satplot.visualiser.assets.widgets as widgets

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
		self.mouseOverText = widgets.PopUpTextBox(v_parent=self.canvas.scene,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)
		self.mouseOverTimer = QtCore.QTimer()
		self.mouseOverTimer.timeout.connect(self._setMouseOverVisible)
		self.mouseOverObject = None

		hlayout1.addStretch()
		hlayout1.addWidget(self.canvas.native)
		hlayout1.addStretch()
		vlayout.addLayout(hlayout1)

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

		# Show the dialog as a modal dialog (blocks the main window)
		self.window.setLayout(vlayout)
		self.window.exec_()

	def save(self):
		dflt_path = satplot_paths.data_dir/'screenshots'
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

