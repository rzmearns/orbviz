
import satplot.visualiser.utils as vis_utils
import satplot.visualiser.Assets as assets
import satplot.visualiser.basevisualiser as basevisualiser
import satplot.visualiser.colours as colours

import logging
logger = logging.getLogger(__name__)


class HistoryVisualiser(basevisualiser.Base):

	def __init__(self, description, ignore_list=[], subplot=False, subplot_args=[None, 111]):
		raise NotImplementedError()

	def set_source(self, source):
		raise NotImplementedError()

	def draw(self, cursor_val=0, redraw=False):
		raise NotImplementedError()

	def set_dflt_options(self):
		""" Sets the default options for a history visualiser
		"""
		raise NotImplementedError()

	def _create_opt_help(self):
		raise NotImplementedError()