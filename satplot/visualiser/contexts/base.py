from abc import ABC, abstractmethod
import numpy as np

from PyQt5 import QtWidgets, QtCore
import json

class BaseContext(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name=None):

		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QHBoxLayout(self.widget)


		# dict storing crucial data for this context
		self.data = {}
		self.data['name'] = name

		self.load_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None

	@abstractmethod
	def saveState(self):
		raise NotImplementedError()
	
	@abstractmethod
	def loadState(self):
		raise NotImplementedError()

	@abstractmethod
	def connectControls(self):
		raise NotImplementedError()

	@abstractmethod
	def _loadData(self):
		raise NotImplementedError()

	def _setUpLoadWorkerThread(self):
		''' call this after setting up the data to load in the inheriting class
			ensure that load_worker has been created before calling this function
			ensure that any slots are connected before calling
			call using super()._loadData()'''
		if self.load_worker is None:
			raise ValueError('Must create load_worker before calling super()._loadData()')
		self.load_worker_thread = QtCore.QThread()

		# Move to new thread and setup signals
		self.load_worker.moveToThread(self.load_worker_thread)
		self.load_worker_thread.started.connect(self.load_worker.run)
		self.load_worker_thread.finished.connect(self.load_worker_thread.deleteLater)
		self.load_worker.finished.connect(self._cleanUpLoadWorkerThread)
		self.load_worker.finished.connect(self.load_worker.deleteLater)
		self.load_worker.error.connect(self._cleanUpLoadWorkerThread)
		self.load_worker.error.connect(self.load_worker.deleteLater)	

	def _cleanUpLoadWorkerThread(self):
		self.load_worker_thread.quit()
		self.load_worker_thread.deleteLater()
		self.load_worker_thread = None
		self.load_worker = None

	def prepSerialisation(self):
		state = {}
		state['data'] = self.data
		return state


class BaseDataWorker(QtCore.QObject):
	finished = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal()

	@abstractmethod
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@abstractmethod
	def run(self):
		raise NotImplementedError()
	
class BaseControls:
	@abstractmethod
	def __init__(self, context_name, *args, **kwargs):
		self.context_name = context_name
		# dict storing config state for this context
		self.state = {}
		self._buildActionDict()

	def _buildActionDict(self):
		with open(f'resources/actions/all.json','r') as fp:
			all_action_dict = json.load(fp)
		with open(f'resources/actions/{self.context_name}.json','r') as fp:
			context_action_dict = json.load(fp)
		self.action_dict = {**all_action_dict, **context_action_dict}