from vispy import app, use

from satplot.visualiser import window

from PyQt5 import QtWidgets, QtCore

import numpy as np

import sys
import argparse

import satplot.visualiser.controls.console as console
import satplot

import json
import pickle
import dill
import datetime as dt

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
		self.save_file = None

	def run(self):
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self):
		for context_key, context in self.window.contexts_dict.items():
			context.connectControls()
			self._connectAllContextControls(context)
			context.controls.toolbar.addButtons()
			context.controls.menubar.addMenuItems()	

	def _connectAllContextControls(self, context):
		context.controls.action_dict['save']['callback'] = self.save
		context.controls.action_dict['save-as']['callback'] = self.saveAs
		context.controls.action_dict['load']['callback'] = self.load

	def save(self):
		if self.save_file is not None:
			self._saveState()
		else:
			self.saveAs()

	def saveAs(self):
		dflt_save_file = f'satplot-state_{dt.datetime.now().strftime("%y%m%d-%H%M%S")}.pickle'
		save_file = self._openFileDialog('SatPlot Save...', 'data/saves/', dflt_save_file)
		if save_file != '':
			self.save_file = save_file
			self._saveState()

	def _saveState(self):
		console.send(f'Saving State to {self.save_file}')
		state = self.window.serialiseContexts()
		with open(self.save_file, 'wb') as picklefp:
			pickle.dump(state, picklefp)

	def load(self):
		load_file = self._openFileDialog('SatPlot Load...', 'data/saves/', None, save=False)
		if load_file != '':
			self._loadState(load_file)

	def _loadState(self, load_file):
		console.send(f'Loading State from {load_file}')
		with open(load_file, 'rb') as picklefp:
			state = pickle.load(picklefp)
		self.window.deserialiseContexts(state)

	def _openFileDialog(self, caption, dir, dflt_filename, save=True):
		if dflt_filename is None:
			dflt_filename = ''
		options = QtWidgets.QFileDialog.Options()
		options |= QtWidgets.QFileDialog.DontUseNativeDialog
		if save:
			filename, _ = QtWidgets.QFileDialog.getSaveFileName(None, 
																caption,
																f'{dir}{dflt_filename}',
																"pickles (*.pickle)",
																options=options)
		else:		
			filename, _ = QtWidgets.QFileDialog.getOpenFileName(None, 
																caption,
																f'{dir}',
																"pickles (*.pickle)",
																options=options)			
		return filename


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



