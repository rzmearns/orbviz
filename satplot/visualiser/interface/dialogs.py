import json
import os
import numpy as np
import pathlib
import pickle
from PIL import Image
import os

import PyQt5.QtWidgets as QtWidgets
from vispy import scene

import satplot
import satplot.util.hashing as satplot_hashing
import satplot.util.paths as satplot_paths
import satplot.visualiser.cameras.RestrictedPanZoom as RestrictedPanZoom

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
	def __init__(self, img_data, img_metadata):
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

