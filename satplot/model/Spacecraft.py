import numpy as np

import importlib
import os


# from thermpy.solver.finite_elements.bulkNode import BulkNode

import logging

logger = logging.getLogger(__name__)


class Spacecraft(object):

	def __init__(self, orbit=None, pointing=None, units='m'):
		raise NotImplementedError()

class GroupLengthException(Exception):
	pass


class DimensionTooGreatException(Exception):
	pass


class MeshNotSpecifiedException(Exception):
	pass

	
class ViewFactorException(Exception):
	pass
