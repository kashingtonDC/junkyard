
import os
import gzip
import shutil
import ftplib
import datetime
import subprocess 

from tqdm import tqdm

# Helpers 

def login_to_ftp(ftproot,data_dir):
	'''
	Use ftplib to login to the NSIDC ftp server, return ftp object cd'd into data dir 
	'''
	f = ftplib.FTP(ftproot)
	f.login()
	f.cwd(data_dir)
	return f

def download_snodat(yeardir, ftp, writedir):
	'''
	Given list of the directories containing data for each year, navigate to each dir, download files, return list of files downloaded 
	'''
	ftp.cwd(yeardir)
	months = [x for x in ftp.nlst() if "." not in x]

	print("Processing SNODAS for {}".format(yeardir))

	allfiles = []
	for month in months[:]:
		monthdir = os.path.join(yeardir,month)
		ftp.cwd(monthdir)
		mfiles = [x for x in ftp.nlst() if x.endswith("tar")]
		for mf in tqdm(mfiles[:]): 
			outfn = os.path.join(writedir,mf)
			with open(outfn, 'wb') as fp:
				ftp.retrbinary('RETR {}'.format(mf), fp.write)
		allfiles.append(mfiles)
	
	print("Wrote SNODAS files for {}".format(yeardir))
	return  [os.path.join(writedir,x) for x in os.listdir(writedir) if x.endswith(".tar")]

def extract_snofiles(filelist, writedir):
	'''
	For the files that have been downloaded, (0) untar file, (1) extract desired variables, (2) convert to gtiff, (2) save, and write to write_dir
	'''

	for file in filelist:
		subprocess.Popen(['tar', '-xvf', file, "-C", writedir],stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

	print("extracted tar files in {}".format(writedir))
	return [os.path.join(writedir,x) for x in os.listdir(writedir) if x.endswith(".gz")]


def process_snofiles(gz_files, variables = ["1025", "1034", "1050"]):
	'''
	1025: Precipitation X 
	1034: Snow water equivalent X 
	1036: Snow depth
	1038: Snow pack average temperature
	1039: Blowing snow sublimation 
	1044: Snow melt
	1050: Snow pack sublimation X
	'''
	
	# Filter files based on vars
	t = [x[x.find("ssmv")+5:x.find("ssmv")+9] for x in gz_files]
	filtered_files = [x[0] for x in zip(gz_files,t) if any(c in x[1] for c in variables)]
	# Unzip
	unzipped_files = []

	for file in filtered_files:
		print(file)
		outfn = os.path.splitext(file)[0]
		print(outfn)
		with gzip.open(file, 'r') as f_in, open(outfn, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
			unzipped_files.append(outfn)

	# Remove the gz files
	for gz in gz_files:
		os.remove(gz)

	return [[x for x in unzipped_files if x.endswith(".dat")],[x for x in unzipped_files if x.endswith(".txt")]]

def txt2hdr(txtfiles, writedir):
	dates = [x[x.find("TS")+2:x.find("TS")+10] for x in txtfiles]
	ymd = [datetime.datetime.strptime(x, '%Y%m%d') for x in dates]
	hdrfiles = []
	# Account for the absurd datum change in 2013... 
	for date,file in zip(ymd, txtfiles):
		if date < datetime.datetime(2013, 10, 1):
			hdrfile = os.path.join(writedir,"../pre_10_2013.hdr")
		if date >= datetime.datetime(2013, 10, 1):
			hdrfile = os.path.join(writedir,"../post_10_2013.hdr")
		
		# Spec dest file
		snofn = os.path.split((os.path.splitext(file)[0]))[1] + ".hdr"
		snowpath = os.path.join(writedir,snofn)
		hdrfiles.append(snowpath)
		shutil.copy(hdrfile,snowpath)

	return hdrfiles

def dat2tif(datfiles, writedir):

	prod_lookup = dict({
	"1025": "PREC",
	"1034": "SNWE",
	"1036": "SNOD",
	"1038": "SPAT",
	"1039": "BlSS",
	"1044": "SMLT",
	"1050": "SSUB",
	})
	
	outfnsv1 = {}

	for file in datfiles:
		date= file[file.find("TS")+2:file.find("TS")+10]
		for k,v in prod_lookup.items():
			if k in file:
				outfnsv1[file] = date+v+".tif"

	outfnsvf = {}
	for k,v in outfnsv1.items():
		if "PREC" in v:
			if "L01" in k:
				outfnsvf[k] = os.path.join(writedir,os.path.splitext(v)[0]+"LQD.tif")

			if "L00" in k:
				outfnsvf[k] = os.path.join(writedir,os.path.splitext(v)[0]+"SOL.tif")
		else:
			outfnsvf[k]= os.path.join(writedir,v)

	for infile, outfile in outfnsvf.items():
		cmd = '''gdal_translate -of GTiff -a_srs '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs' -a_nodata -9999 -a_ullr -124.73333333 52.87500000 -66.94166667 24.95000000 {} {}'''.format(infile,outfile)
		print(cmd)
		os.system(cmd)

	oldfiles = [os.path.join(writedir,x) for x in os.listdir(writedir) if not x.endswith(".tif")]
	for old in oldfiles:
		os.remove(old)
		# print(old)

	return outfnsvf.values()

def clip_tifs(tifs,dst_dir, shapefile = "/Users/aakash/Desktop/SatDat/SNODAS/shape/cvws.shp"):
	if not os.path.exists(dst_dir):
		os.mkdir(dst_dir)

	for tif in tifs:
		cmd = '''gdalwarp -cutline {} -crop_to_cutline {} {}'''.format(shapefile,tif, os.path.join(dst_dir,os.path.split(tif)[1]))
		print(cmd)
		os.system(cmd)

def main():

	# Download SNODAS files from colorado ftp
	ftproot = 'sidads.colorado.edu'
	data_dir = '/DATASETS/NOAA/G02158/masked/'
	writedir = os.path.join(os.getcwd(),'SNODAS')
	if not os.path.exists(writedir):
		os.mkdir(writedir)


	ftp = login_to_ftp(ftproot,data_dir)
	dirlist = ftp.nlst()
	yeardirs = [os.path.join(data_dir,x) for x in dirlist if "." not in x]
	for y in yeardirs[:1]:
		tarfiles = download_snodat(y, ftp, writedir = writedir)
		gz_files = extract_snofiles(tarfiles, writedir = writedir)
		datfiles,txtfiles = process_snofiles(gz_files)
		hdrfiles = txt2hdr(txtfiles, writedir = writedir)
		tiffiles = dat2tif(datfiles, writedir = writedir)
		clipped = clip_tifs(tiffiles, dst_dir = "/Users/aakash/Desktop/SatDat/SNODAS/CA_DAT")

if __name__ == '__main__':
	main()