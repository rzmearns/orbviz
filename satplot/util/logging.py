import datetime as dt
import logging
import satplot.util.paths as satplot_paths

def setUpLogLevels():

	# 3rd party libraries
	logging.getLogger('pyopengl').setLevel(logging.DEBUG)
	logging.getLogger('numpy').setLevel(logging.ERROR)
	logging.getLogger('scipy').setLevel(logging.ERROR)
	logging.getLogger('skyfield').setLevel(logging.ERROR)
	logging.getLogger('PyQt5').setLevel(logging.WARNING)
	logging.getLogger('hapsira').setLevel(logging.ERROR)
	logging.getLogger('spacetrack').setLevel(logging.WARNING)
	logging.getLogger('vispy').setLevel(logging.WARNING)

	# spherapy

	# satplot
	logging.getLogger('satplot.visualiser.interface').setLevel(logging.INFO)


def configureLogger():
	# Create handlers
	stdout_handler = logging.StreamHandler()
	stdout_handler.setLevel(logging.WARNING)
	stdout_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
	stdout_handler.setFormatter(stdout_format)

	static_file_handler = logging.FileHandler(f"{satplot_paths.data_dir}/logs/satplot.log",mode='w')
	static_file_handler.setLevel(logging.DEBUG)
	static_file_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
	static_file_handler.setFormatter(static_file_format)

	# Add handlers to the logger
	root_logger = logging.getLogger()
	root_logger.handlers.clear()

	root_logger.setLevel(logging.DEBUG)
	root_logger.addHandler(stdout_handler)
	root_logger.addHandler(static_file_handler)

	setUpLogLevels()