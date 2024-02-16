# Generic exceptions that apply throughout satplot.

class InputException(Exception):
	'''Input is not valid
	'''
	pass

class OutOfRange(Exception):
	'''The value is out of the acceptable range
	'''
	pass

class DimensionError(Exception):
	'''Dimension of an array is invalid
	'''
	pass
	
class GeometryError(Exception):
	'''For when a user tries to do something non-Euclidean
	'''
	pass