import os
import subprocess
import shlex

link = 'https://lpdaacsvc.cr.usgs.gov/appeears/api/bundle/b3184ac2-77c0-4676-8f58-d38a19a83ddb/c919309d-c156-4f76-8467-c80df4a95125/MOD16A2GF.006_ET_500m_doy2010001_aid0001.tif'

command = '''curl {} -o asdf.tif'''.format(link)

subprocess.call(shlex.split(command))


