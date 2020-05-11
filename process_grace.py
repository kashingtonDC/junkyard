import os
import gdal
import numpy as np

def array2raster(rasterfn,newRasterfn,array):
	raster = gdal.Open(rasterfn)
	geotransform = raster.GetGeoTransform()
	proj = raster.GetProjection()
	originX = geotransform[0]
	originY = geotransform[3]
	pixelWidth = geotransform[1]
	pixelHeight = geotransform[5]
	cols = raster.RasterXSize
	rows = raster.RasterYSize

	driver = gdal.GetDriverByName('GTiff')
	outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Int16) # Change dtype here
	outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
	outband = outRaster.GetRasterBand(1)
	outband.WriteArray(array)
		
	outRaster.SetProjection(proj)
	outband.FlushCache()

def read_as_array(raster):
	ds = gdal.Open(raster)
	array = np.array(ds.GetRasterBand(1).ReadAsArray())
	return array


files = [x for x in os.listdir(os.getcwd()) if x.endswith(".tif")]


# Scale 
globalmax = 0
globalmin = 0

print('scaling')


for i in files[:]:
	
	dat = read_as_array(i)
	dat[dat == -99999.0] = 0

	currentmax = np.max(dat)
	currentmin = np.min(dat)
	
	if currentmax > globalmax:
		globalmax = currentmax

	if currentmin < globalmin:
		globalmin = currentmin


print("global min = {}" .format(globalmin))
print("global max = {}" .format(globalmax))

denominator = globalmax - globalmin

for i in files[:]:
	print("processing {}".format(i))
	
	# Setup out filename
	fn = i
	outfn = fn[:-4] + "_proc.tif"

	# read file scale, convert

	dat = read_as_array(i)
	dat[dat == -99999.0] = np.nan

	print(np.nanmean(dat))

	scaled = np.interp(dat, (dat.min(), dat.max()), (0, 65535))
	scaled[scaled == np.nan] = 0

	# scaled = (dat - globalmin) / denominator * 65535
	out = scaled.astype(int)

	# write 
	array2raster(i, outfn, out)

	print('done ================' *5)