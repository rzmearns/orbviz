from abc import ABC, abstractmethod


class Base(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self):
		pass

	@abstractmethod
	def setDefaultOptions(self):
		""" Set the default options for the visualiser {dict} """

	@abstractmethod
	def setSource(self):	
		""" Set the data source object for the visualiser """

	@abstractmethod
	def draw(self):
		""" (Re)Draw onto the axes """

	@abstractmethod
	def _createOptHelp(self):
		""" Create help for all the default options {dict} """