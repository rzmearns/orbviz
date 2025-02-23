import argparse
import datetime as dt
import pathlib
import pickle
import warnings

from PyQt5 import QtWidgets, QtCore
from vispy import app, use

import satplot
from satplot.visualiser.contexts.canvas_wrappers.base_cw import (BaseCanvas)
import satplot.visualiser.interface.console as console
import satplot.visualiser.interface.dialogs as dialogs
import satplot.visualiser.window as window


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
		satplot.threadpool = QtCore.QThreadPool()
		print(f"Creating threadpool with {satplot.threadpool.maxThreadCount()} threads")

	def run(self) -> None:
		self.window.show()
		self.pyqt_app.run()

	def _connectControls(self) -> None:
		for context in self.window.contexts_dict.values():
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
		console.send(f'Saving State to {self.save_file}')
		state = self.window.serialiseContexts()
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
		console.send(f'Loading State from {load_file}')
		with open(load_file, 'rb') as picklefp:
			state = pickle.load(picklefp)
		self.window.deserialiseContexts(state)

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

def setDefaultPackageOptions() -> None:
	satplot.running = True
	satplot.gl_plus = True
	satplot.debug = False
	try:
		with open('data/spacetrack/.credentials', 'rb') as fp:
			satplot.spacetrack_credentials = pickle.load(fp)
	except Exception:
		satplot.spacetrack_credentials = {'user':None, 'passwd':None}

if __name__ == '__main__':
	setDefaultPackageOptions()
	parser = argparse.ArgumentParser(
						prog='SatPlot',
						description='Visualisation software for satellites; including orbits and pointing.')
	parser.add_argument('--nogl+', action='store_true', dest='nogl_plus')
	parser.add_argument('--debug', action='store_true', dest='debug')
	args = parser.parse_args()
	if args.nogl_plus:
		satplot.gl_plus = False
	if args.debug:
		satplot.debug = True
	application = Application()
	application.run()



