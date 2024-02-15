import numpy as np
import plotly.graph_objs as go
import plotly.offline
import datetime as dt


import os, sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5 import QtWebEngineWidgets
import time

class FigureViewer(QtWebEngineWidgets.QWebEngineView):
	def __init__(self, fig, exec=True):

		self.app = None
		self.env_ipython = None
		self.file_path = None

		self.setEnv()

		# Create a QApplication instance or use the existing one if it exists
		self.app = QApplication.instance() if QApplication.instance() else QApplication(sys.argv)

		super().__init__()


		self.setFigure(fig)
		print(f"create window: {dt.datetime.now()}")
		self.update()
		print(f"finish load html: {dt.datetime.now()}")
		self.show()
		print(f"finish render: {dt.datetime.now()}")


		if not self.env_ipython:
			if exec:
				self.app.exec_()

	def closeEvent(self, event):
		os.remove(self.file_path)

	def setEnv(self):
		self.env_ipython = False
		try:
			from IPython import get_ipython
		except:			
			# can't be running in Ipython
			return
		ipython = get_ipython()
		if ipython is not None:
			self.env_ipython = True
			ipython.magic("gui qt5")
			return

	def update(self):
		print(f"start create html: {dt.datetime.now()}")
		self.file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp.html"))
		plotly.offline.plot(self.fig, filename=self.file_path, auto_open=False)
		print(f"start load html: {dt.datetime.now()}")
		self.load(QUrl.fromLocalFile(self.file_path))

	def setFigure(self, fig):
		self.fig = fig

	def setTitle(self, title: str):
		pass

	def setWindowTitle(self, title: str):
		self.setWindowTitle(title)