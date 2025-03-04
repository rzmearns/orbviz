# Generic exceptions that apply throughout satplot.

class InputError(Exception):
	'''Input is not valid
	'''
	pass

class OutOfRangeError(Exception):
	'''The value is out of the acceptable range
	'''
	pass

class DimensionError(Exception):
	'''Dimension of an array is invalid
	'''
	pass

class InvalidDataError(Exception):
	'''Data model is incorrect or doesn't exist
	'''
	pass
	
class GeometryError(Exception):
	'''For when a user tries to do something non-Euclidean
	'''
	pass


class ConcaveError(GeometryError):
	'''For when a user tries to define something that is non-Euclidean.'''
	pass


class NonPolygonError(GeometryError):
	'''Raised when trying to apply a function which operates on polygons to a non polygon'''
	pass


class ViewFactorError(GeometryError):
	'''Raised when there is an error in viewfactor calculations'''
	pass
