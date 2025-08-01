from abc import abstractmethod
import logging
import traceback

import typing
from typing import Any

from PyQt5 import QtCore

from satplot.model.data_models.data_types import DataType
import satplot.visualiser.interface.console as console

logger = logging.getLogger(__name__)

class BaseDataModel(QtCore.QObject):
	data_ready = QtCore.pyqtSignal()
	data_err = QtCore.pyqtSignal()
	index_updated = QtCore.pyqtSignal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = {'data_type': DataType.BASE,
						'is_data_valid': False}

	def _setConfig(self, param:str, val:Any) -> None:
		self.config[param] = val
		self.config['is_data_valid'] = False

	def updateConfig(self, param:str, val:Any) -> None:
		if param not in self.config.keys():
			logger.error("%s not a valid configuration option for %s", param, self.config['data_type'])
			raise ValueError(f"{param} not a valid configuration option for {self.config['data_type']}")
		self._setConfig(param, val)

	def isValid(self) -> bool:
		return self.config['is_data_valid']

	def getType(self) -> DataType:
		return self.config['data_type']

	def getConfigValue(self, value:str) -> Any:
		# TODO: check if value is a key of self.config
		return self.config[value]

	def _displayError(self, err:tuple) -> None:
		exctype = err[0]
		value = err[1]
		traceback = err[2]
		logger.error(value)
		console.send(value)
		self.data_err.emit()

	def updateIndex(self, index:int) -> None:
		self.curr_index = index
		self.index_updated.emit()

	@abstractmethod
	def prepSerialisation(self) -> dict[str, Any]:
		raise NotImplementedError()

	def deSerialise(self, state:dict) -> None:
		for k,v in state['config'].items():
			self.updateConfig(k,v)

	def printConfig(self) -> None:
		print(f"Data Config for {self.getConfigValue('data_type')}")
		for k,v in self.config.items():
			print(f'\t{k}:{v}')