import numpy as np

primitive_types = (int, float, str, bool, np.number, np.character, np.bool_)
delimiter = ','


def isPrimitive(val) -> bool:
	return isinstance(val, primitive_types)

def float2TableRow(float_val, precision) -> str:
	return f'{float_val:.{precision}f}'

def list2TableRow(list_val, precision) -> str:
	s = '['
	for ii, el in enumerate(list_val):
		if not isPrimitive(el):
			raise TypeError(f"A table row cannot format nested complex types, found {type(el)} inside a list")

		s += _formatPrimitiveVal(list_val, precision)

		# don't delimit last value
		if ii < len(list_val)-1:
			s += f'{delimiter} '

	s += ']'
	return s

def tuple2TableRow(tuple_val, precision) -> str:
	s = '('
	for ii, el in enumerate(tuple_val):
		if not isPrimitive(el):
			raise TypeError(f"A table row cannot format nested complex types, found {type(el)} inside a tuple")

		s += _formatPrimitiveVal(el, precision)

		# don't delimit last value
		if ii < len(tuple_val)-1:
			s += f'{delimiter} '

	s += ')'
	return s

def ndarray2TableRow(ndarr, precision) -> str:
	dim = len(ndarr.shape)
	if dim < 1:
		raise TypeError(f'A table row cannot format an array with no dimensions, found {dim}')
	if dim > 2:
		raise TypeError(f'A table row cannot format an array with more than 2 dimensions, found {dim}')

	s = ''
	max_val_str_len = len(f'{_formatPrimitiveVal(ndarr.max(), precision)}')
	min_val_str_len = len(f'{_formatPrimitiveVal(ndarr.min(), precision)}')
	max_width = max(max_val_str_len, min_val_str_len)

	if dim == 1:
		s += '['
		for ii in range(ndarr.shape[0]):
			s += _formatPrimitiveVal(ndarr[ii], precision, max_width)
			if ii < ndarr.shape[0]-1:
				s += f'{delimiter} '
		s += ']'


	elif dim == 2:
		s += '['
		for ii in range(ndarr.shape[0]):
			s += '['
			for jj in range(ndarr.shape[1]):

				s += _formatPrimitiveVal(ndarr[ii,jj], precision, max_width)
				if jj < ndarr.shape[1]-1:
					s += f'{delimiter} '
			s += ']'
			if ii < ndarr.shape[0]-1:
				s += '\n '
		s += ']'

	return s

def _formatPrimitiveVal(val, precision, width=0) -> str:
	if isinstance(val, str|np.character):
		return f'{val}'
	elif isinstance(val, bool|np.bool_):
		return f'{val}'
	elif isinstance(val, int|float|np.number):
		return f'{val:{width}.{precision}f}'
	else:
		return f'{val}'