import os
from bs4 import BeautifulSoup, SoupStrainer
import requests
 
grace_url = 'https://podaac-opendap.jpl.nasa.gov/opendap/allData/tellus/L3/grace/land_mass/RL06/v03/JPL/contents.html'
base_url = 'https://podaac-opendap.jpl.nasa.gov/opendap/hyrax/allData/tellus/L3/grace/land_mass/RL06/v03/JPL/'
 
fns = []
 
for link in BeautifulSoup(requests.get(grace_url).text, 'html.parser', parse_only=SoupStrainer('a')):
    if link.has_attr('href'):
        contents = link.get('href')
        if contents.endswith(".tif"):
            if "opendap" not in contents:
                fns.append(contents)
 
print("Found {} files to download".format(str(len(fns))))

print(fns)
 
dl_urls = [os.path.join(base_url,x) for x in fns][:4]
 
for idx, x in enumerate(dl_urls):
    print("downloading {}".format(fns[idx]))
    command = 'curl -o {} {}'.format(fns[idx], dl_urls[idx])
    os.system(command)