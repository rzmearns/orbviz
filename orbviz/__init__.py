from importlib import metadata
import pathlib

import platformdirs

version = '0.3'
running = True
debug = False
gl_plus = True
high_precision = False
threadpool = None

service_name = "orbviz"
service_author = "rzmm"

try:
	__version__ = metadata.version(service_name)
except metadata.PackageNotFoundError:
	print(f'Version of {service_name} is uknown') #noqa: T201
	__version__ = "x.x.x"


data_dir = pathlib.Path(platformdirs.user_data_dir(appname=service_name,
															ensure_exists=True))