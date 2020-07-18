#sample raster to points
from PIL import Image
import numpy as np
import ogr, os, gdal, osr
import math

inputRaster="C:\\Users\\hamelac1\\sync\\LERC\\Tappino\\TVS_GeoRes\\sites\\tap03\\tap03w\\output\\tap03w.tif" 
outputShape="C:\\Users\\hamelac1\\sync\\LERC\\Tappino\\TVS_GeoRes\\sites\\tap03\\TestMerge\\tap03w.shp"

gcpfile="C:\\Users\\hamelac1\\sync\\LERC\\Tappino\\TVS_GeoRes\\sites\\tap03\\tap03_w\\output\\gcp.txt"

def gcp2twf(gcpfile,raster):
	cellsizeX=1
	cellsizeY=1
	gcp=open(gcpfile,"r")
	gcp1=gcp.readline().strip().split("\t")
	gcp2=gcp.readline().strip().split("\t")
	deltax=float(gcp1[0])-float(gcp2[0])-(float(gcp1[2])-float(gcp2[2]))
	deltay=float(gcp1[1])-float(gcp2[1])-(float(gcp1[3])-float(gcp2[3]))
	if deltax==0:
		teta=0
	else:
		teta=math.atan(deltay/deltax)
	print deltax,deltay
	A=math.cos(teta)*cellsizeX
	B=-math.sin(teta)*cellsizeX
	D=-math.sin(teta)*cellsizeY
	E=-math.cos(teta)*cellsizeY
	print (A,B,D,E)
	#for gp1
	d=math.sqrt(np.power((float(gcp1[0])),2)+np.power((float(gcp1[1])),2))
	if float(gcp1[0])==0:
		teta_img=0
	else:
		teta_img=math.atan(float(gcp1[0])/float(gcp1[1]))
	tetasum=teta-teta_img
	C=(-math.sin(tetasum)*d)+float(gcp1[2])
	F=(math.cos(tetasum)*d)+float(gcp1[3])
	
	print (C,F)
	#need to write the TWF file with ABDECF
	
def raster2pointShp(inputRaster, outputShape):
	try:
		print (inputRaster.split(".")[0])
		worldFile=open(inputRaster.split(".")[0]+".tfwx", "r")

	except:
		print ("Could not find the World file")
	else:
		A=float(worldFile.readline().replace(',','.'))
		D=float(worldFile.readline().replace(',','.'))
		B=float(worldFile.readline().replace(',','.'))
		E=float(worldFile.readline().replace(',','.'))
		C=float(worldFile.readline().replace(',','.'))
		F=float(worldFile.readline().replace(',','.'))
		worldFile.close()
		im = Image.open(inputRaster)
		imarray=np.array(im)
		
		
		# Input data
		fieldName = 'Value'
		fieldType = ogr.OFTInteger
		fieldValue = 'value'
		shpDriver = ogr.GetDriverByName("ESRI Shapefile")
		if os.path.exists(outputShape):
			shpDriver.DeleteDataSource(outputShape)
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(32633)
		outDataSource = shpDriver.CreateDataSource(outputShape)
		layer = outDataSource.CreateLayer(outputShape, geom_type=ogr.wkbPoint )
		idField = ogr.FieldDefn(fieldName, fieldType)
		layer.CreateField(idField)

		for i in range (0,imarray.shape[1]):
			for ii in range (0,imarray.shape[0]):
				if int(imarray[ii][i])>0:
					# create the feature
					featureDefn = layer.GetLayerDefn()
					feature = ogr.Feature(featureDefn)
					# Set the attributes using the values from the delimited text file
					
					feature.SetField("Value", int(imarray[ii][i]))

					x=A*i+B*ii+C
					y=D*i+E*ii+F
					# create the WKT for the feature using Python string formatting
					wkt = "POINT(%f %f)" %  (x , y)
					#print (int(imarray[i][ii]),float(Xtl-math.cos(xrot)*cellSizeX*ii) , float(Ytl-math.cos(yrot)*cellSizeY*i))

					# Create the point from the Well Known Txt
					point = ogr.CreateGeometryFromWkt(wkt)

					# Set the feature geometry using the point
					feature.SetGeometry(point)
					# Create the feature in the layer (shapefile)
					layer.CreateFeature(feature)
					# Destroy the feature to free resources
					feature.Destroy()
				


		# Destroy the data source to free resources
		outDataSource.Destroy()
		
def raster2pointXYZ(inputRaster, outputShape):
	try:
		print (inputRaster.split(".")[0])
		worldFile=open(inputRaster.split(".")[0]+".tfwx", "r")

	except:
		print ("Could not find the World file")
	else:
		A=float(worldFile.readline().replace(',','.'))
		D=float(worldFile.readline().replace(',','.'))
		B=float(worldFile.readline().replace(',','.'))
		E=float(worldFile.readline().replace(',','.'))
		C=float(worldFile.readline().replace(',','.'))
		F=float(worldFile.readline().replace(',','.'))
		worldFile.close()
		im = Image.open(inputRaster)
		imarray=np.array(im)
		
		
		# Input data
		fieldName = 'Value'
		fieldType = ogr.OFTInteger
		fieldValue = 'value'
		output='"X","Y","Value"\n'

		for i in range (0,imarray.shape[1]):
			for ii in range (0,imarray.shape[0]):
				if int(imarray[ii][i])>0:s
					x=A*i+B*ii+C
					y=D*i+E*ii+F
					output+="%s,%s,%s\n" %(x,y,imarray[ii][i])
				


		# Destroy the data source to free resources
		outDataSource.Destroy()
		
raster2point(inputRaster, outputShape)
#gcp2twf(gcpfile,inputRaster)
print ("Done")