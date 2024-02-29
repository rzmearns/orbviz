from abc import ABC, abstractmethod


class BaseAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self):
		pass

	@abstractmethod
	def draw(self):
		""" Draw asset onto the canvas"""
		raise NotImplementedError

	@abstractmethod
	def compute(self):
		"""compute the asset geometry"""
		raise NotImplementedError

	@abstractmethod
	def recompute(self):
		""" recompute the asset geometry"""
		raise NotImplementedError

	@abstractmethod
	def _createOptHelp(self):
		""" Create help for all the default options {dict} """
		raise NotImplementedError
	
	@abstractmethod
	def _setDefaultOptions(self):
		""" Set the default options for the visualiser {dict} """
		raise NotImplementedError
