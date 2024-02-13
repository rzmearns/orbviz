
import thermpy.visualiser.utils as vis_utils
import thermpy.visualiser.Assets as assets
import thermpy.visualiser.basevisualiser as basevisualiser
import thermpy.visualiser.colours as colours

import logging
logger = logging.getLogger(__name__)


class HistoryVisualiser(basevisualiser.Base):

	def __init__(self, description, ignore_list=[], subplot=False, subplot_args=[None, 111]):
		if not subplot:
			self.label_str = description
			vis_utils.create_figure(self.label_str, description, three_dim=False)
		else:
			self.label_str = subplot_args[0]
			vis_utils.create_figure(self.label_str, description, three_dim=False, subplot_pos=subplot_args[1])

		self.description = description
		self.subplot_pos = subplot_args[1]			
		self.set_dflt_options()
		self.fig = vis_utils.find_figure(self.label_str)
		self.ax = vis_utils.find_axes(self.label_str, self.subplot_pos)
		
		self.actors = {}
		self.ignore_list = ignore_list
		self.source = None
		self.cursor = assets.Cursor2D(self, self.ax, 0, vert=True)
		self.drawn = False

	def set_source(self, source):
		self.source = source

	def draw(self, cursor_val=0, redraw=False):
		if not self.drawn or redraw:
			descr = self.description.split('_')[0]
			if len(self.source.datashape) == 2:
				m, n = self.source.datashape
				for ii in range(m):
					for jj in range(n):
						if ii == m - 1 and jj == n - 1:
							label = f'Space Node self {descr}'
						if ii == m - 1:
							label = f'Space Node to Node {jj} {descr}'
						elif jj == n - 1:
							label = f'Node {ii} to Space Node {descr}'
						else:
							label = f'Node {ii} to Node {jj} {descr}'
						col_index = ii * m + jj
						if ii not in self.ignore_list:
							self.ax.plot(self.source.timespan.seconds_since_start(), self.source.history[:, ii, jj],
									color=colours.get_numbered_colour(col_index), linestyle=colours.get_numbered_linestyle(col_index),
									label=label)
			else:
				n, = self.source.datashape
				for ii in range(n):
					if ii == n - 1:
						label = f'Space Node'
					else:
						descr = self.description.split('_')[0]
						label = f'Node {ii} ({self.source.node_descriptions[ii]}) {descr}'
					if ii not in self.ignore_list:
						self.ax.plot(self.source.timespan.seconds_since_start()[:-1], self.source.history[:-1, ii],
								color=colours.get_numbered_colour(ii), linestyle=colours.get_numbered_linestyle(ii),
								label=label)
			self.ax.set_xlabel(self.opts['x_units'])
			self.ax.set_ylabel(self.opts['y_units'])
			self.ax.legend()

		if 'cursor' in self.actors.keys():
			self.actors['cursor'].remove()
			del self.actors['cursor']

		# TODO: 
		# if self.opts['draw_cursor']:
		self.actors['cursor'] = self.cursor.draw(cursor_val)

		if not self.drawn:
			self.drawn = True

	def set_dflt_options(self):
		""" Sets the default options for a history visualiser
		"""
		self._dflt_opts = {}
		
		# TODO: Add flags to options for drawing gizmo and sun
		self._dflt_opts['x_units'] = ''
		self._dflt_opts['y_units'] = ''
		self._dflt_opts['z_units'] = ''

		self.opts = self._dflt_opts.copy()
		self._create_opt_help()

	def _create_opt_help(self):
		while True:
			try:
				self.opts_help = {}
				self.opts_help['x_units'] = "Unit to be displayed on x axis. dflt: '{opt}'.".format(opt=self._dflt_opts['x_units'])
				self.opts_help['y_units'] = "Unit to be displayed on y axis. dflt: '{opt}'.".format(opt=self._dflt_opts['y_units'])
				self.opts_help['z_units'] = "Unit to be displayed on z axis. dflt: '{opt}'.".format(opt=self._dflt_opts['z_units'])
				break
			except AttributeError:
				logger.debug("Options not yet set - setting.")
				self.set_dflt_options()

		if self.opts_help.keys() != self._dflt_opts.keys():
			logger.warning("Options help are not set for every option which exists. Missing {list}".format(list=set(self._dflt_opts.keys()) - set(self.opts_help.keys())))
