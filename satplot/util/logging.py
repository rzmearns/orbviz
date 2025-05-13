import datetime as dt
import logging
import satplot.util.paths as satplot_paths

def setUpLogLevels():

	# 3rd party libraries
	logging.getLogger('numpy').setLevel(logging.ERROR)
	logging.getLogger('scipy').setLevel(logging.ERROR)
	logging.getLogger('skyfield').setLevel(logging.ERROR)
	logging.getLogger('PyQt5').setLevel(logging.ERROR)
	logging.getLogger('hapsira').setLevel(logging.ERROR)
	logging.getLogger('spacetrack').setLevel(logging.WARNING)
	logging.getLogger('vispy').setLevel(logging.WARNING)

	# spherapy

	# satplot


def configureLogger():
	# Create handlers
	# c_handler = logging.StreamHandler()
	# # f_handler = logging.FileHandler(f"{satplot_paths.data_dir}/logs/satplot-{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.log")
	# f_static_handler = logging.FileHandler(f"{satplot_paths.data_dir}/logs/satplot.log",mode='w')
	# c_handler.setLevel(logging.WARNING)
	# f_static_handler.setLevel(logging.DEBUG)

	# # Create formatters and add it to handlers
	# c_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
	# f_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
	# c_handler.setFormatter(c_format)
	# # f_handler.setFormatter(f_format)
	# f_static_handler.setFormatter(f_format)

	# logger = logging
	# # Add handlers to the logger
	# logger.addHandler(c_handler)
	# # logger.addHandler(f_handler)
	# logger.addHandler(f_static_handler)

	logger = logging
	logger.basicConfig(filename=f"{satplot_paths.data_dir}/logs/satplot.log",
						filemode='w',
						format='%(name)s:%(levelname)s: %(message)s',
						level=logging.DEBUG)

	setUpLogLevels()