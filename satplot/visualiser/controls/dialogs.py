import PyQt5.QtWidgets as QtWidgets
# import QApplication, QMainWindow, QPushButton, QDialog, QVBoxLayout, QLabel, QWidget
import satplot
import pickle
import os

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
			os.remove(credential_file)

	def cancel(self):
		self.window.close()
