import traceback
from PyQt5 import QtCore
from abc import ABC, abstractmethod

from satplot.model.data_models.data_types import DataType
import satplot.visualiser.interface.console as console

from typing import Any

class BaseDataModel(QtCore.QObject):
	data_ready = QtCore.pyqtSignal()
	data_err = QtCore.pyqtSignal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.config = {'data_type': DataType.BASE,
						'is_data_valid': False}

	def _setConfig(self, param:str, val:Any) -> None:
		self.config[param] = val
		self.config['is_data_valid'] = False

	def updateConfig(self, param:str, val:Any) -> None:
		if param not in self.config.keys():
			raise ValueError(f"{param} not a valid configuration option for {self.config['data_type']}")
		self._setConfig(param, val)

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

	def printConfig(self):
		print(f"Data Config for {self.getConfigValue('data_type')}")
		for k,v in self.config.items():
			print(f'\t{k}:{v}')