import satplot.util.spacetrack as spacetrack
import satplot.visualiser.interface.console as console
import requests

MAX_RETRIES=3

def updateTLEs(sat_config,user=None, passwd=None):
	sat_id_list = spacetrack.getSatIDs(sat_config)
	console.send(f"Using CELESTRAK to update TLEs for {sat_config['name']}")
	for sat_id in sat_id_list:
		url = f'https://celestrak.org/NORAD/elements/gp.php?CATNR={sat_id}'
		for ii in range(MAX_RETRIES):
			r = requests.get(url)
			if r.status_code == 200:
				break
		
		if ii == MAX_RETRIES-1:
			raise ValueError(f'Could not fetch celestrak information for sat_id: {sat_id}')
		
		fname = getTLEFilePath(sat_id)
		dat_list = r.text.split('\r\n')
		with open(fname, 'w') as fp:
			fp.write(f'0 {dat_list[0].rstrip()}\n')
			fp.write(f'{dat_list[1].rstrip()}\n')
			fp.write(f'{dat_list[2].rstrip()}')
		

def getTLEFilePath(sat_id):
	return f'data/TLEs/{sat_id}.temptle'