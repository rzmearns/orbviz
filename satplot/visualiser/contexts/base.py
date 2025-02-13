from abc import ABC, abstractmethod
import numpy as np

from PyQt5 import QtWidgets, QtCore
import json
import sys

class BaseContext(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name=None):

		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QHBoxLayout(self.widget)


		# dict storing crucial configuration data for this context
		self.config = {}
		self.config['name'] = name

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
	def _configureData(self):
		raise NotImplementedError()

	def prepSerialisation(self):
		state = {}
		state['data'] = self.data
		return state

	def deSerialise(self, state):
		pass
	
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