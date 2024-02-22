from abc import ABC, abstractmethod


class BaseAsset(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self):
		pass

	@abstractmethod
	def redraw(self):
		""" (Re)Draw onto the axes
		 	Used after either a display style is changed, or recompute is called when the underlying geometry has been modified"""
		raise NotImplementedError

	@abstractmethod
	def recompute(self):
		""" recompute the underlying geometry"""
		raise NotImplementedError

	@abstractmethod
	def _createOptHelp(self):
		""" Create help for all the default options {dict} """
		raise NotImplementedError
	
	@abstractmethod
	def setDefaultOptions(self):
		""" Set the default options for the visualiser {dict} """
		raise NotImplementedError
