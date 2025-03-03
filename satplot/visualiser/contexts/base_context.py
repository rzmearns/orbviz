from abc import ABC, abstractmethod
import json
from typing import Any

from PyQt5 import QtWidgets


class BaseContext(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, data=None):

		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QHBoxLayout(self.widget)
		self.window = None
		self.controls = None

		# dict storing crucial configuration data for this context
		self.config = {}
		self.config['name'] = name
		self.sccam_state = None
		self.canvas_wrapper = None
		self.data = None
		self.load_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None

	@abstractmethod
	def saveState(self) -> None:
		raise NotImplementedError()
	
	@abstractmethod
	def loadState(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def connectControls(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def _configureData(self) -> None:
		raise NotImplementedError()

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}
		state['data'] = self.data
		return state

	def deSerialise(self, state_dict):
		pass
	
class BaseControls:
	@abstractmethod
	def __init__(self, context_name:str, *args, **kwargs):
		self.context_name = context_name
		# dict storing config state for this context
		self.state = {}
		self.action_dict = {}
		self._buildActionDict()

	def _buildActionDict(self) -> None:
		with open(f'resources/actions/all.json','r') as fp:
			all_action_dict = json.load(fp)
		with open(f'resources/actions/{self.context_name}.json','r') as fp:
			context_action_dict = json.load(fp)
		self.action_dict = {**all_action_dict, **context_action_dict}