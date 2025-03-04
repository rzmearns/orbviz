import pathlib
import os

satplot_dir = pathlib.Path(f'{os.path.dirname(os.path.abspath(__file__))}').parent.resolve()
data_dir = pathlib.Path(f'{satplot_dir.parent}/data')
