import logging

import orbviz.util.paths as orbviz_paths


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

	# orbviz

	logging.getLogger('orbviz.visualiser').setLevel(logging.WARNING)
	# logging.getLogger('orbviz.visualiser.window').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.assets').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.assets.spacecraft').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.cameras').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.contexts').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.contexts.canvas_wrappers').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.interface').setLevel(logging.INFO)
	# logging.getLogger('orbviz.visualiser.shells').setLevel(logging.INFO)
	logging.getLogger('orbviz.model.data_models').setLevel(logging.INFO)
	logging.getLogger('orbviz.model.geometry').setLevel(logging.WARNING)
	logging.getLogger('orbviz.model.lens_models').setLevel(logging.WARNING)

def configureLogger():
	# Create handlers
	stdout_handler = logging.StreamHandler()
	stdout_handler.setLevel(logging.WARNING)
	stdout_format = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
	stdout_handler.setFormatter(stdout_format)

	static_file_handler = logging.FileHandler(f"{orbviz_paths.data_dir}/logs/orbviz.log",mode='w')
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