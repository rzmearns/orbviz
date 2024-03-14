from vispy import app, use

from satplot.visualiser import window

from PyQt5 import QtWidgets, QtCore

import numpy as np

import sys
import argparse

import satplot.visualiser.controls.console as console
import satplot

import json

import warnings
warnings.filterwarnings("ignore", message="Optimal rotation is not uniquely or poorly defined for the given sets of vectors.")

use(gl='gl+')

class Application():
	def __init__(self) -> None:
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()
		self.window = window.MainWindow(title="Sat Plot")

		self._connectControls()
		self.load_data_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self):
		for context_key, context in self.window.context_dict.items():
			context.connectControls()
			self._connectAllContextControls(context)
			context.controls.toolbar.addButtons()
			context.controls.menubar.addMenuItems()	

	def _connectAllContextControls(self, context):
		context.controls.action_dict['save']['callback'] = self._saveState
		context.controls.action_dict['load']['callback'] = self._loadState

	def _saveState(self):
		console.send(f'Saving State - Not Implemented')

	def _loadState(self):
		console.send(f"loading state - Not Implemented")


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
						prog='SatPlot',
						description='Visualisation software for satellites; including orbits and pointing.')
	parser.add_argument('--nogl+', action='store_true', dest='nogl_plus')
	parser.add_argument('--debug', action='store_true', dest='debug')
	args = parser.parse_args()
	if args.nogl_plus:
		satplot.gl_plus = False
	else:
		satplot.gl_plus = True
	if args.debug:
		satplot.debug = True
	else:
		satplot.debug = False
	application = Application()
	application.run()



