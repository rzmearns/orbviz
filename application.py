import argparse
import datetime as dt
import logging
import pathlib
import pickle
import warnings

import typing
from typing import Any

import PIL

from PyQt5 import QtCore, QtWidgets

from vispy import app, use

import satplot
import satplot.util.logging as satplot_logging
import satplot.util.threading as threading
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.dialogs as dialogs
import satplot.visualiser.window as window

logger = logging.getLogger('satplot')

warnings.filterwarnings("ignore", message="Optimal rotation is not uniquely or poorly defined for the given sets of vectors.")
satplot_logging.configureLogger()
use(gl='gl+')

class Application():
	def __init__(self) -> None:
		satplot.threadpool = threading.Threadpool()
		logger.info("Creating threadpool with %s threads",satplot.threadpool.maxThreadCount())
		self.pyqt_app = app.use_app("pyqt5")
		self.pyqt_app.create()
		self.window = window.MainWindow(title="Sat Plot")

		self._connectControls()
		self.load_data_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None
		self.save_file = None


	def run(self) -> None:
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self) -> None:
		for shell in self.window.shell_dict.values():
			for context in shell.contexts_dict.values():
				context.connectControls()
				self._connectAllContextControls(context)
				context.controls.toolbar.addButtons()
				context.controls.menubar.addMenuItems()

	def _connectAllContextControls(self, context:BaseCanvas) -> None:
		if context.controls is not None:
			context.controls.action_dict['save']['callback'] = self.save
			context.controls.action_dict['save-as']['callback'] = self.saveAs
			context.controls.action_dict['load']['callback'] = self.load
			context.controls.action_dict['spacetrak-credentials']['callback'] = dialogs.SpaceTrackCredentialsDialog
		else:
			logger.error('context: %s does not have an associated action dictionary from a resources/actions/<context>.json file.',context)
			raise ValueError()


	def save(self) -> None:
		if self.save_file is not None:
			self._saveState()
		else:
			self.saveAs()

	def saveAs(self) -> None:
		dflt_save_file = f'satplot-state_{dt.datetime.now().strftime("%y%m%d-%H%M%S")}.pickle'
		save_file = self._openFileDialog('SatPlot Save...', pathlib.Path('data/saves/'), dflt_save_file)
		if save_file.name != '':
			self.save_file = save_file
			self._saveState()

	def _saveState(self) -> None:
		logger.info('Saving State to %s', self.save_file)
		console.send(f'Saving State to {self.save_file}')
		state = self.prepSerialisation()
		if self.save_file is not None:
			with open(self.save_file, 'wb') as picklefp:
				pickle.dump(state, picklefp)
		else:
			# TODO: DO SOMETHING
			pass

	def load(self) -> None:
		load_file = self._openFileDialog('SatPlot Load...', pathlib.Path('data/saves/'), None, save=False)
		if load_file != '':
			self._loadState(load_file)

	def _loadState(self, load_file:pathlib.Path) -> None:
		logger.info('Loading State from %s', load_file)
		console.send(f'Loading State from {load_file}')
		with open(load_file, 'rb') as picklefp:
			state = pickle.load(picklefp)
		self.deSerialise(state)


	def _openFileDialog(self, caption: str, dir:pathlib.Path, dflt_filename:str|None, save=True) -> pathlib.Path:
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
		return pathlib.Path(filename)

	def prepSerialisation(self) -> dict[str, Any]:
		state = {}
		state['window_contexts'] = self.window.serialiseContexts()
		state['metadata'] = {}
		state['metadata']['version'] = satplot.version
		state['metadata']['gl_plus'] = satplot.gl_plus
		return state

	def deSerialise(self, state:dict[str, Any]) -> None:
		if state['metadata']['version'] != satplot.version:
			logger.error("This satplot state was not created with this version of satplot: file %s, satplot %s",state['metadata']['version'], satplot.version)

		if state['metadata']['gl_plus'] != satplot.gl_plus:
			logger.error("WARNING: this file was created with a different GL mode: GL+ = %s. It may not load correctly.", satplot.gl_plus)


		self.window.deserialiseContexts(state['window_contexts'])

def setDefaultPackageOptions() -> None:
	satplot.running = True
	satplot.gl_plus = True
	satplot.debug = False
	satplot.high_precision = False
	PIL.Image.MAX_IMAGE_PIXELS = None

if __name__ == '__main__':
	setDefaultPackageOptions()
	parser = argparse.ArgumentParser(
						prog='SatPlot',
						description='Visualisation software for satellites; including orbits and pointing.')
	parser.add_argument('--nogl+', action='store_true', dest='nogl_plus')
	parser.add_argument('--high_precision', action='store_true', dest='high_precision')
	parser.add_argument('--debug', action='store_true', dest='debug')
	args = parser.parse_args()
	if args.nogl_plus:
		satplot.gl_plus = False
	if args.high_precision:
		satplot.high_precision = True
	if args.debug:
		satplot.debug = True
	logger.info("Satplot:")
	logger.info("\tVersion: %s", satplot.version)
	application = Application()
	application.run()



