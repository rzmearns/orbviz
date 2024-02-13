def printLine(line,descr_str=''):
	'''
	Prints the point with a descriptive string
	"Descriptive string:[x,y,z]
						[x,y,z]""

	Parameters
	----------
	line: (2,3) ndarray
		
	descr_str: string
		descriptive string

	Returns
	-------	
	'''

	print_str=descr_str+":[%f,%f,%f]"
	spacing_str=" "*len(descr_str)+":[%f,%f,%f]"
	print(print_str %line[0,0],line[0,1],line[0,2])
	print(spacing_str %line[1,0],line[1,1],line[1,2])

def printPoint(point,descr_str=''):
	'''
	Prints the point with a descriptive string
	"Descriptive string:[x,y,z]""

	Parameters
	----------
	point: (3,) ndarray
		
	descr_str: string
		descriptive string

	Returns
	-------	
	'''

	print_str=descr_str+":[%f,%f,%f]"
	print(print_str %point[0],point[1],point[2])

def printPoly(poly,descr_str=''):
	'''
	Prints the point with a descriptive string
	"Descriptive string:[x,y,z]
						.......
						[x,y,z]""

	Parameters
	----------
	line: (n,3) ndarray
		
	descr_str: string
		descriptive string

	Returns
	-------	
	'''

	print_str=descr_str+":[%f,%f,%f]"
	spacing_str=" "*len(descr_str)+":[%f,%f,%f]"
	print(print_str %poly[0,0],poly[0,1],poly[0,2])
	for ii in range(1,len(poly)):
		print(spacing_str %poly[1,0],poly[1,1],poly[1,2])
		
def printScalar(scalar,descr_str=''):
	'''
	Prints the point with a descriptive string
	"Descriptive string:[x,y,z]""

	Parameters
	----------
	scalar: float
		
	descr_str: string
		descriptive string

	Returns
	-------	
	'''

	print_str=descr_str+":%f"
	print(print_str %scalar)