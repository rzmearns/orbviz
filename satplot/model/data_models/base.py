import traceback
from PyQt5 import QtCore
from abc import ABC, abstractmethod

from satplot.model.data_models.data_types import DataType
import satplot.visualiser.controls.console as console

class BaseDataModel(QtCore.QObject):
	data_ready = QtCore.pyqtSignal()
	data_err = QtCore.pyqtSignal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = {'data_type': DataType.BASE,
						'is_data_valid': False}

	def updateConfig(self, param, val):
		"""[summary]

		[description]

		Args:
			param ([type]): [description]
			val ([type]): [description]
		"""
		self.config[param] = val
		self.config['is_data_valid'] = False

	def isValid(self):
		return self.config['is_data_valid']

	def getType(self):
		return self.config['data_type']

	def getConfigValue(self, value):
		# TODO: check if value is a key of self.config
		return self.config[value]

	def _displayError(self, err:tuple):
		exctype = err[0]
		value = err[1]
		traceback = err[2]
		console.send(value)
		self.data_err.emit()

	@abstractmethod
	def serialise(self):
		raise NotImplementedError()

	@abstractmethod
	def deSerialise(self):
		raise NotImplementedError()


	# def _setUpLoadWorkerThread(self):
	# 	''' call this after setting up the data to load in the inheriting class
	# 		ensure that load_worker has been created before calling this function
	# 		call using super()._setUpLoadWorkerThread()'''
	# 	if self.load_worker is None:
	# 		raise ValueError('Must create load_worker before calling super()._setUpLoadWorkerThread()')
	# 	self.load_worker_thread = QtCore.QThread(parent=self.window)
	# 	# Move to new thread and setup signals
	# 	self.load_worker.moveToThread(self.load_worker_thread)
	# 	self.load_worker_thread.started.connect(self.load_worker.run)
	# 	self.load_worker_thread.finished.connect(self.load_worker_thread.deleteLater)
	# 	self.load_worker.finished.connect(self._cleanUpLoadWorkerThread)
	# 	self.load_worker.finished.connect(self._updateDataSources)
	# 	self.load_worker.finished.connect(self._updateControls)
	# 	self.load_worker.error.connect(self._cleanUpErrorInLoadWorkerThread)

	# def _cleanUpLoadWorkerThread(self):
	# 	if self.load_worker_thread is not None:
	# 		self.load_worker_thread.quit()
	# 		self.load_worker_thread.deleteLater()
	# 	self.load_worker_thread = None
	# 	self.load_worker = None

	# def _cleanUpErrorInLoadWorkerThread(self, err_str=None):
	# 	print(f'Clean Up Load Worker Thread Error: {err_str}', file=sys.stderr)
	# 	return self._cleanUpLoadWorkerThread()
