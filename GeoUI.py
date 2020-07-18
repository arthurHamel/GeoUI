import sys
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog, QMessageBox, QLabel, QDialog, QMainWindow, QAction, QMenu
import os
import numpy as np
#import FileDialog
from matplotlib.figure import Figure
import matplotlib.cm as cm
import matplotlib
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.patches as patches



DIAG_Import, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'importlogger.ui'))


class ImportDialog(QDialog, DIAG_Import):
	def __init__(self, parent=None):
		"""Constructor."""
		super(ImportDialog, self).__init__(parent)
		# Set up the user interface from Designer.
		# After setupUI you can access any designer object by doing
		# self.<objectname>, and you can use autoconnect slots - see
		# http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
		# #widgets-and-dialogs-with-auto-connect
		self.setupUi(self)
		self.setWindowTitle('Import data')
	
DIAG_Settings, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'settings.ui'))


class SettingsDialog(QDialog, DIAG_Settings):
	def __init__(self, parent=None):
		"""Constructor."""
		super(SettingsDialog, self).__init__(parent)
		# Set up the user interface from Designer.
		# After setupUI you can access any designer object by doing
		# self.<objectname>, and you can use autoconnect slots - see
		# http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
		# #widgets-and-dialogs-with-auto-connect
		self.setupUi(self)
		self.setWindowTitle('Settings')
 
DIAG_Assemble, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'assemble.ui'))


class Assemble(QDialog, DIAG_Assemble):
	def __init__(self, parent=None):
		"""Constructor."""
		super(Assemble, self).__init__(parent)
		# Set up the user interface from Designer.
		# After setupUI you can access any designer object by doing
		# self.<objectname>, and you can use autoconnect slots - see
		# http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
		# #widgets-and-dialogs-with-auto-connect
		self.setupUi(self)
		

class Survey(object):
	def __init__(self, path, sitename):
		self.foldername=path
		self.pathRaw=path +"/raw/"
		self.pathOutput=path +"/output/"
		self.sitename=sitename
		self.gridSize=(20,20)
	
	
	def getGeometry(self):
		index=np.genfromtxt(str(self.pathOutput)+'geometry.txt',dtype='str', delimiter="\t");
		return index;
	
	
class Process:
	def despike(self, array):

		from PIL import Image
		print ('despiking...')
		cols=array.shape[0]
		rows=array.shape[1]
		despikeArray=array
		despikeLog=np.zeros(array.shape)
		despikeIdx=np.zeros(array.shape)
		mask=np.zeros(array.shape)
		count=0
		countFail=0
		errorLog=""
		treshold=3
		for x in range (0, cols-1):
			for y in range (0, rows-1):
				if array[x][y]<0:
					array[x][y]=0		#Negative values are treated as zeros
		
		for x in range (0, cols-1):
			for y in range (0, rows-1):
				value=array[x][y]
				if x==0:
					neighbours=np.array([array[x][y-1],array[x+1][y-1],array[x+1][y],array[x][y+1],array[x+1][y+1]])
				elif x==cols-1:
					neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x-1][y],array[x-1][y+1],array[x][y+1]])
				elif y==0:
					neighbours=np.array([array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
				elif y==rows-1:
					neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y]])
				else:
					neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
				if value==0 and  np.count_nonzero(neighbours)<4:
					despikeIdx[x][y]=1
				else:
					win3=np.append(neighbours,value)
				
					if (np.count_nonzero(neighbours)>4):
						mean=sum(neighbours[np.nonzero(neighbours)])/float(np.count_nonzero(neighbours))
						std=np.std(neighbours[np.nonzero(neighbours)])
						b= np.where((neighbours<mean+treshold*std) & (neighbours>mean-treshold*std) & (neighbours>0.01))	
						reliableNeighbours=neighbours[b]
						if (len(reliableNeighbours)<3):
							countFail+=1
							print (value,"could not be despiked")
							x_error=x%20
							y_error=y%20
							gridID=w.getGeometry()[int(x/20)][int(y/20)]
							errorLog+= ('%s: could not be could not be despiked at %s-%s in grid %s\n' %(value,x_error,y_error,gridID))
							despikeIdx[x][y]=7
						else:
							mean=sum(reliableNeighbours[np.nonzero(reliableNeighbours)])/float(np.count_nonzero(reliableNeighbours))
							std=np.std(reliableNeighbours[np.nonzero(reliableNeighbours)])
							if ((value>mean+treshold*std) | (value<mean-treshold*std)):
								if value==0:
									despikeIdx[x][y]=2
								else:
									despikeIdx[x][y]=3
					else: 
						if value!=0:
							despikeIdx[x][y]= 4
						elif value<0 : #or value > or < to the standart deviation of the whole grid.
							despikeIdx[x][y]= 5
						else:
							despikeIdx[x][y]= 6
							
						# Index:  0 good data. no despiking
								# 1 no data
								# 2 zero can be extrapolated
								# 3 odd value can be deskiped
								# 4 maybe odd but not enough neigbours
								# 5 should not be corrected but still too odd
								# 6 zero with not enough neighbours
					
		for x in range (0, cols-1):
			for y in range (0, rows-1):
				
				if (despikeIdx[x][y]>1) & (despikeIdx[x][y]!=6):
					value=array[x][y]
					
					if x==0:
						neighbours=np.array([array[x][y-1],array[x+1][y-1],array[x+1][y],array[x][y+1],array[x+1][y+1]])
					elif x==cols-1:
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x-1][y],array[x-1][y+1],array[x][y+1]])
					elif y==0:
						neighbours=np.array([array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
					elif y==rows-1:
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y]])
					else:
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
					
					if x==0:
						neighboursIdx=np.array([despikeIdx[x][y-1],despikeIdx[x+1][y-1],despikeIdx[x+1][y],despikeIdx[x][y+1],despikeIdx[x+1][y+1]])
					elif x==cols-1:
						neighboursIdx=np.array([despikeIdx[x-1][y-1],despikeIdx[x][y-1],despikeIdx[x-1][y],despikeIdx[x-1][y+1],despikeIdx[x][y+1]])
					elif y==0:
						neighboursIdx=np.array([despikeIdx[x-1][y],despikeIdx[x+1][y],despikeIdx[x-1][y+1],despikeIdx[x][y+1],despikeIdx[x+1][y+1]])
					elif y==rows-1:
						neighboursIdx=np.array([despikeIdx[x-1][y-1],despikeIdx[x][y-1],despikeIdx[x+1][y-1],despikeIdx[x-1][y],despikeIdx[x+1][y]])
					else:
						neighboursIdx=np.array([despikeIdx[x-1][y-1],despikeIdx[x][y-1],despikeIdx[x+1][y-1],despikeIdx[x-1][y],despikeIdx[x+1][y],despikeIdx[x-1][y+1],despikeIdx[x][y+1],despikeIdx[x+1][y+1]])
					
					b= np.where((neighboursIdx==0)) #and maybe 4?
					if len(neighbours[b])>2:
						despikeArray[x][y]=np.mean(neighbours[b])
					else:
						despikeArray[x][y]=np.mean(neighbours)
						x_error=x%20
						y_error=y%20
						gridID=w.survey.getGeometry()[int(x/20)][int(y/20)]
						print ('Warning not enough points (%s, val:%s) at %s-%s in grid %s' %(len(neighbours[b]),value,x_error,y_error,gridID))
					
				# if (np.count_nonzero(neighbours)>5):
					# mean=sum(neighbours)/float(len(neighbours))
					# std=np.std(neighbours)

					# b= np.where((neighbours<mean+treshold*std) & (neighbours>mean-treshold*std) & (neighbours>0.01))
		
					# reliableNeighbours=neighbours[b]
					
					# if (value>mean+treshold*std or value<mean-treshold*std or value<2):
						# if (len(reliableNeighbours)>3):
							# despikeArray[x][y]=np.mean(reliableNeighbours)
							# count+=1
							# despikeLog[x][y]=(mean-value)/std
							# if despikeArray[x][y]<0:
								# countFail+=1
								# print (value,"desiked but still wrong")
								# x_error=x%20
								# y_error=y%20
								# gridID=self.getGeometry()[int(x/20)][int(y/20)]
								# errorLog+= ('%s: could not be could not be despiked (??) at %s-%s in grid %s\n' %(value,x_error,y_error,gridID) )
						# else:
							# countFail+=1
							# print (value,"could not be despiked")
							# x_error=x%20
							# y_error=y%20
							# gridID=self.getGeometry()[int(x/20)][int(y/20)]
							# errorLog+= ('%s: could not be could not be despiked (no reliable neighbours) at %s-%s in grid %s\n' %(value,x_error,y_error,gridID) )
					# else:
						# despikeArray[x][y]=value
						
				# else:
						# despikeArray[x][y]=value
						# if despikeArray[x][y]<0:
								# countFail+=1
								# gridID=self.getGeometry()[int(x/20)][int(y/20)]
								# x_error=x%20
								# y_error=y%20
								# errorLog+= ('%s: could not be could not be despiked (on the edge) at %s-%s in grid %s\n' %(value,x_error,y_error,gridID) )
		# for x in range (0, cols-1):
			# for y in range (0, rows-1):
				# if despikeArray[x][y]<0:
					# countFail+=1
					# gridID=self.getGeometry()[int(x/20)][int(y/20)]
					# x_error=x%20
					# y_error=y%20
					# errorLog+=("%s: could not be despiked (on the edge) at %s-%s in grid %s\n" %(value,x_error,y_error,gridID) )
		# self.addInfo("%s values despiked.\n" %count)
		# print("%s values despiked." %count)
		# if countFail>0:
			# msg=QMessageBox.about(self, "Remaining odds", ("%s values could not be despiked:\n%s" %(countFail,errorLog)))
		# min,max=np.min(despikeArray),np.max(despikeArray)
		# print ("despike min max",min,max)
		# mask[np.where(despikeLog==0)]=255
		# mask = Image.fromarray(mask).convert('L')
		
		#idx = Image.fromarray(despike).convert('L')
		# return despikeIdx
		return despikeArray
	
	def hillshade(self,array, azimuth, angle_altitude, z): 
		from numpy import gradient
		from numpy import pi
		from numpy import arctan
		from numpy import arctan2
		from numpy import sin
		from numpy import cos
		from numpy import sqrt
		from numpy import zeros
		from numpy import uint8
			
		nodata=(array!=0)
		array=z*array
		x, y = gradient(array)
		slope = pi/2. - arctan(sqrt(x*x + y*y))
		aspect = arctan2(-x, y)
		azimuthrad = azimuth*pi / 180.
		altituderad = angle_altitude*pi / 180.
			 
		 
		shaded = sin(altituderad) * sin(slope)\
		+ cos(altituderad) * cos(slope)\
		* cos(azimuthrad - aspect)
			
		shaded=255*(shaded+1)/2		#255*(shaded + 1)/2
		shaded[shaded<1]=1
		
		
		cols=array.shape[0]
		rows=array.shape[1]
		count=0
		countFail=0
		for x in range (0, cols-1):
			for y in range (0, rows-1):
				value=array[x][y]
				if (value!=0):
					if (x==0):
						neighbours=np.array([array[x][y-1],array[x+1][y-1],array[x+1][y],array[x][y+1],array[x+1][y+1]])
					elif (y==0):
						neighbours=np.array([array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
					elif (x==cols-1):
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x-1][y],array[x-1][y+1],array[x][y+1]])
					elif (y==rows-1):
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y]])
					else:
						neighbours=np.array([array[x-1][y-1],array[x][y-1],array[x+1][y-1],array[x-1][y],array[x+1][y],array[x-1][y+1],array[x][y+1],array[x+1][y+1]])
					if 0 in neighbours:
						if (x==0):
							shade_neighbrs=np.array([shaded[x][y-1],shaded[x+1][y-1],shaded[x+1][y],shaded[x][y+1],shaded[x+1][y+1]])
						elif (y==0):
							shade_neighbrs=np.array([shaded[x-1][y],shaded[x+1][y],shaded[x-1][y+1],shaded[x][y+1],shaded[x+1][y+1]])
						elif (x==cols-1):
							shade_neighbrs=np.array([shaded[x-1][y-1],shaded[x][y-1],shaded[x-1][y],shaded[x-1][y+1],shaded[x][y+1]])
						elif (y==rows-1):
							shade_neighbrs=np.array([shaded[x-1][y-1],shaded[x][y-1],shaded[x+1][y-1],shaded[x-1][y],shaded[x+1][y]])
						else:
							shade_neighbrs=np.array([shaded[x-1][y-1],shaded[x][y-1],shaded[x+1][y-1],shaded[x-1][y],shaded[x+1][y],shaded[x-1][y+1],shaded[x][y+1],shaded[x+1][y+1]])
						
						shaded[x][y]=np.mean(shade_neighbrs[np.nonzero(neighbours)])
						count+=1
						
		print (" %s edges" %count)					
		return shaded*nodata
			
	def localVariation(self, matrix):
		import scipy.ndimage

		lowpass = scipy.ndimage.gaussian_filter(matrix, 5)
		gauss_highpass = matrix - lowpass
		
		return gauss_highpass
	
	



Ui_MainWindow, QtBaseClass = uic.loadUiType(os.path.join(
	os.path.dirname(__file__), 'mainwindow.ui'))
 
class MyApp(QMainWindow, Ui_MainWindow):
	def __init__(self):
		QMainWindow.__init__(self)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)
		
		self.setWindowTitle('GeoProcessing') 
		
		self.dirSelect_main.clicked.connect(self.select_output)
		self.process_main.clicked.connect(self.process)
		self.exportGeoTiff_main.clicked.connect(self.exportGeo)
		self.actionImport_main.triggered.connect(self.importDialog)
		self.actionSettings.triggered.connect(self.settingsDialog)
		self.actionAssemble_main.triggered.connect(self.assembleDialog)
		self.getStats_main.triggered.connect(self.makeStatistics)
		self.exportGeoTiff_main.setEnabled(False)
		self.loadParam()
		
		#Create the toolbar
		
		actionRotateR = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'ressources/rotateR.png')), 'Rotate clockwise', self)
		actionRotateL = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'ressources/rotateL.png')), 'Rotate counter clockwise', self)
		actionFlipUD = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'ressources/flipud.png')), 'Flip vertical', self)
		actionFlipLR = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'ressources/fliplr.png')), 'Flip horiziontal', self)
		#Icon from https://www.iconfinder.com/icons/281321/adjust_align_control_editor_manage_move_operate_rotate_icon#size=128
	
	
		actionRotateR.triggered.connect(self.rotateR)
		actionRotateL.triggered.connect(self.rotateL)
		actionFlipUD.triggered.connect(self.flipud)
		actionFlipLR.triggered.connect(self.fliplr)
		
		
		self.figure = plt.figure()
		self.canvas = FigureCanvas(self.figure)
		 # set button context menu policy
		self.canvas.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.canvas.customContextMenuRequested.connect(self.on_context_menu)

		# create context menu
		self.popMenu = QMenu(self)
		self.actionOpenEditor=QAction('Open grid in editor', self)
		self.actionEditPoint=QAction('Edit point', self)
		self.popMenu.addAction(self.actionOpenEditor)
		self.popMenu.addAction(self.actionEditPoint)
		self.actionOpenEditor.triggered.connect(self.openEditor)
		self.actionEditPoint.triggered.connect(self.editPoint)
	 

		   


		self.toolbar = NavigationToolbar(self.canvas, self)
		self.toolbar.addAction(actionRotateL)
		self.toolbar.addAction(actionRotateR)
		self.toolbar.addAction(actionFlipUD)
		self.toolbar.addAction(actionFlipLR)
		
		self.canvasLayout.addWidget(self.toolbar)
		self.canvasLayout.addWidget(self.canvas)
		self.sizeTiles_lbl.setText("x:%s y:%s" %(self.tileSize[0], self.tileSize[0]))
		self.epsg_txt.setText("EPSG: %s" %(self.epsg))

		self.stdClip_val.setText(str(self.stdClip_slider.value()/float(100)))
		self.stdClip_slider.valueChanged.connect(self.changeClipValue)
		
		self.stdClip_check.toggled.connect(self.clipChecked)
		self.survey=Survey(self.foldername, self.siteName)
		
		
		self.statusBar().showMessage('Ready')
		self.gridSize=(20,20)
		
	def clipChecked(self):
		if self.stdClip_check.isChecked():
			self.stdClip_slider.setEnabled(True)
			self.stdClip_val.setEnabled(True)
			#Update view
		else:
			self.stdClip_slider.setEnabled(False)
			self.stdClip_val.setEnabled(False)
		
	def changeClipValue(self):
		self.stdClip_val.setText(str(self.stdClip_slider.value()/float(100)))
		
	def addInfo(self,l):
		self.infotxt+=l
		self.infoTxt_main.setText(self.infotxt)
		app.processEvents()
		
	def clearInfo(self):
		self.infotxt=""
		self.infoTxt_main.setText(self.infotxt)
		app.processEvents()
		

	def select_output(self):

		foldername = QFileDialog.getExistingDirectory(self, "Select output directory ",self.foldername)
		self.foldername=foldername
		#Here check that the directory is valid
		self.pathRaw=foldername +"/raw/"
		self.pathOutput=foldername +"/output/"
		infotxt=""
		if (os.path.isdir(self.pathRaw)==0):
			infotxt+="Raw folder not found\n"
		if (os.path.isdir(self.pathOutput)==0):
			infotxt+="Output folder not found\n"		

		if (infotxt!=""):
			QMessageBox.about(self, "Invalid directory", infotxt)
			self.actionImport_main.setEnabled(False)
			self.actionAssemble_main.setEnabled(False)
			self.dir_main.setText("")
		else:
			self.dir_main.setText(foldername)
			self.actionImport_main.setEnabled(True)
			self.actionAssemble_main.setEnabled(True)
			self.siteName=foldername.split("/")[-1]
			self.siteName_main.setText(self.siteName)
			self.saveParam()
			

	def scanLastGridId(self):
		listCsv=os.listdir(self.pathRaw)
		last=0
		for i in range (0,len(listCsv)):
			str=listCsv[i].split(".")
			if (str[1]=="csv"):
				a=str[0].split("_")
				gridId=a[1]
				if ("v" not in gridId) and ("n" not in gridId):
					if (int(gridId)>last):
						last=int(gridId)+1
		return last
		
	def importDialog(self):
		self.dlgImport = ImportDialog()	
		self.siteName=self.siteName_main.text()
		self.dlgImport.exportDir.setText(str(self.siteName))
		self.init=self.scanLastGridId()

		self.dlgImport.firstGrid.setValue(self.init)
		self.dlgImport.go.clicked.connect(self.downloadRM85)
		
		self.dlgImport.show()
		
	def settingsDialog(self):
		self.dlgSettings = SettingsDialog()
		index = self.dlgSettings.epsg.findText(str(self.epsg), QtCore.Qt.MatchFixedString)
		if index >= 0:
			self.dlgSettings.epsg.setCurrentIndex(index)
		# self.dlgSettings.epsg.value(self.epsg)
		self.dlgSettings.go.clicked.connect(self.saveSettingsChanges)
		self.dlgSettings.show()
		
	def saveSettingsChanges(self):
		self.epsg=int(self.dlgSettings.epsg.currentText())
		self.saveParam()
		self.epsg_txt.setText("EPSG: %s" %(self.epsg))
		del self.dlgSettings
		
	def assembleDialog(self):
		self.siteName=str(self.siteName_main.text())
		print (self.siteName)
		self.geoFile="0\t0\t0\t0\t0\n0\t0\t0\t0\t0\n0\t0\t0\t0\t0\n0\t0\t0\t0\t0\n"
		if os.path.isfile(self.foldername+"/output/geometry.txt"):
			f=open(self.foldername+"/output/geometry.txt", "r+")
			self.geoFile=f.read()
			f.close()
		
		else: 
			print ("The geometry file was not found. A new one was initiated.")
			f=open(self.foldername+"/output/geometry.txt", "w+")
			f.write(self.geoFile)
			f.close()

		self.dlgAss = Assemble()
		self.dlgAss.buttonBox.accepted.connect(self.assembleSave)
		self.dlgAss.text.setLineWrapMode(0)
		self.dlgAss.text.appendPlainText(self.geoFile)
		self.dlgAss.show()
			
	def assembleSave(self):
		self.geoFile=self.dlgAss.text.toPlainText()
		f=open(self.foldername+"/output/geometry.txt", "w+")
		f.write(self.geoFile)
		f.close()

	def makeStatistics(self):
		import matplotlib.pyplot as plt
		first=1
		files=os.listdir(self.pathRaw)
		for file in files:
			if ".csv" in file:
				grid=np.genfromtxt(self.pathRaw+file, delimiter=",")
				print (grid.shape)
				if first:
					all=grid
					first=0
				else:
					all=np.concatenate((grid,all))
		
		print (all.shape)
		self.min=all.min()
		self.max=all.max()
		self.std=all.std()
		self.mean=all.mean()
		
		hist, bin_edges = np.histogram(all)
		plt.hist(all, bins=100)
		plt.show()
		
		report=("Statistics\nmin=%.3f\nmax=%.3f\nStd=%.3f\nMean=%.3f" %(self.min,self.max,self.std,self.mean))
		
		self.infoTxt_main.setText(report)
		
	def drawSelection(self):
		
		x,y=self.currentSelection
		if (x!=-1):
			self.select=self.ax.add_patch(
				patches.Rectangle(
					(x*self.tileSize[0], y*self.tileSize[1]),   # (x,y)
					self.tileSize[0],		  # width
					self.tileSize[1],		  # height
					fill=False,
					edgecolor="red",
					linewidth=1
				)
			)
			gridID=self.getGeometry()[y][x]
			print (x,y,gridID)
			self.select_gridID= plt.text(x*self.tileSize[0], y*self.tileSize[1]+self.tileSize[1],gridID)
			self.canvas.draw()
	
	def clearSelection(self):
		x,y=self.currentSelection
		if (x!=-1):
			try:
				self.select.remove()
				self.select_gridID.remove()
				self.canvas.draw()
			except:
				print ("No selection to clear")
	
	def onclickFig(self,event):
		print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
			  (event.button, event.x, event.y, event.xdata, event.ydata))
		selection=True
		if event.button==1:
			if selection:
				x=int(event.xdata/self.tileSize[0])
				y=int(event.ydata/self.tileSize[1])
				print("right Click at %s %s" %(x,y))
				self.clearSelection()
				if self.index[y][x]!="0":
					self.currentSelection=(x,y)
					self.drawSelection()
		
		elif event.button==2:
			self.drag_view(event)
			
		elif event.button==3:
			x=int(event.xdata/self.tileSize[0])
			y=int(event.ydata/self.tileSize[1])
			self.clearSelection()
			if self.index[y][x]!="0":
				self.currentSelection=(x,y)
				self.drawSelection()
				
				point=QPoint(event.x, self.canvas.height()-event.y)
				self.popMenu.exec_(self.canvas.mapToGlobal(point))
			
			
	def drag_view(self, event):
		print ("pan")
		'on button press we will see if the mouse is over us and store some data'
		if event.inaxes != self.ax.axes: return
		cur_xlim = self.ax.get_xlim()
		cur_ylim = self.ax.get_ylim()
		self.press = cur_xlim, cur_ylim, event.xdata, event.ydata

	def on_motion(self, event):
		'on motion we will move the rect if the mouse is over us'
		if self.press is None: return
		if event.inaxes != self.ax.axes: return
		cur_xlim, cur_ylim, xpress, ypress = self.press
		dx = event.xdata - xpress
		dy = event.ydata - ypress
		
		#print('x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f' %
		#	  (x0, xpress, event.xdata, dx, x0+dx))
		self.ax.set_xlim([cur_xlim[0]-dx,cur_xlim[1]-dx])
		self.ax.set_ylim([cur_ylim[0]-dy,cur_ylim[1]-dy])
		app.processEvents()

		self.canvas.draw()

	def on_context_menu(self, point):
		# # show context menu
		# self.popMenu.exec_(self.canvas.mapToGlobal(point)) 
		pass

	def on_release(self, event):
		if event.button==2:
			'on release we reset the press data'
			self.press = None
			print ("realese button")

	def zoom_fun(self,event,base_scale = 1.5):
		dataXmax=self.survey.getGeometry().shape[1]*self.gridSize[1]
		dataYmax=self.survey.getGeometry().shape[0]*self.gridSize[0]

		# get the current x and y limits
		curr_xlim = self.ax.get_xlim()
		curr_ylim = self.ax.get_ylim()
		xdata = event.xdata # get event x location
		ydata = event.ydata # get event y location
		if event.button == 'up':
			# deal with zoom in

			scale_factor = 1/base_scale
		elif event.button == 'down':

			# deal with zoom out
			scale_factor = base_scale
		else:
			# deal with something that should never happen
			scale_factor = 1
			print (event.button)
		# set new limits
		


		new_width = (curr_xlim[1]-curr_xlim[0])*scale_factor
		new_height= (curr_ylim[1]-curr_ylim[0])*scale_factor

		relx = (curr_xlim[1]-event.xdata)/(curr_xlim[1]-curr_xlim[0])
		rely = (curr_ylim[1]-event.ydata)/(curr_ylim[1]-curr_ylim[0])

		new_xlim=[event.xdata-new_width*(1-relx),event.xdata+new_width*(relx)]
		if new_xlim[0]<0:
			new_xlim[0]=0
		if  new_xlim[1]>dataXmax:
			new_xlim[1]=dataXmax
			
		self.ax.set_xlim(new_xlim)
		new_ylim=[event.ydata+new_width*(1-rely),event.ydata-new_width*(rely)]
		if new_ylim[0]<0:
			new_ylim[0]=0
		if  new_ylim[1]>dataYmax:
			new_ylim[1]=dataYmax
		self.ax.set_ylim(new_ylim)
		
		app.processEvents()

		self.canvas.draw()

	
	def rotateL(self):
		ii,i=self.currentSelection
		csv=np.genfromtxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), delimiter=",")
		csv=np.rot90(csv)
		
		np.savetxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), csv, delimiter=",", fmt='%.2f')

		self.process()
		
		self.currentSelection=(ii,i)
		
		self.drawSelection()
	
	def rotateR(self):
		ii,i=self.currentSelection
		csv=np.genfromtxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), delimiter=",")
		csv=np.rot90(csv,3)
		
		np.savetxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), csv, delimiter=",", fmt='%.2f')

		self.process()
		self.currentSelection=(ii,i)
		self.drawSelection()
		
		
	def fliplr(self):
		ii,i=self.currentSelection
		csv=np.genfromtxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), delimiter=",")
		csv=np.fliplr(csv)
		
		np.savetxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), csv, delimiter=",", fmt='%.2f')
		
		self.process()
		self.currentSelection=(ii,i)
		self.drawSelection()
		
	def flipud(self):
		ii,i=self.currentSelection
		csv=np.genfromtxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), delimiter=",")
		csv=np.flipud(csv)
		
		np.savetxt(str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv'), csv, delimiter=",", fmt='%.2f')
		
		self.process()
		self.currentSelection=(ii,i)
		self.drawSelection()
		
	def openEditor(self):
		ii,i=self.currentSelection
		file=str(self.pathRaw+self.siteName+'_'+self.index[i][ii]+'.csv')
		import subprocess
		print (file)
		subprocess.call(['notepad',file])
		
	def editPoint(self):
		print ("the point")
	
	def downloadRM85(self):
		import serial
		
		rows=self.dlgImport.YSize.value()
		cols=self.dlgImport.XSize.value()
		
		
		try:
			ser = serial.Serial(str(self.dlgImport.com.currentText()), int(self.dlgImport.baud.currentText()), timeout=1) #Tried with and without the last 3 parameters, and also at 1Mbps, same happens.
			ser.flushInput()
			ser.flushOutput()
		except:
			connected=0
			self.dlgImport.status.setText("No device detected. Check connection.")
			app.processEvents()
		else:
			self.dlgImport.status.setText("Ready. Press <<Dump>> on device.")
			connected=1
			
		app.processEvents()
		if connected:
			started = 0
			ii=int(self.dlgImport.firstGrid.value())-1
			data_raw=""
			mode= self.dlgImport.mode.currentIndex()
			siteNameID=self.siteName
			while True:

				bytesToRead = ser.readline()
				if (bytesToRead!=""):
					self.dlgImport.status.setText("Loading...")
					app.processEvents()
					started=1
					ii+=1
					if (ii<10):
						countStr=str("0%s" %ii)
					else: 
						countStr=ii
					
					matrix1=np.empty([rows,cols])
					if mode==1:
						matrix50=np.empty([rows,2*cols])
						samplesPerPoints=3
					if mode ==0:
						samplesPerPoints=1
					self.dlgImport.progressBar.setValue(0)
					
					for x in range (0,cols):
						line=""
						self.dlgImport.status.setText("Loading... Grid %s - Line %s" %(ii, x+1))
						for y in range (0,rows):
							for pt in range (0,samplesPerPoints):
								while True:
									if (x==0 and y==0 and pt==0):
										line=str(bytesToRead)
									else:
										line=str(ser.readline())

									reading=str(ser.readline())
									if "01" in reading:
										gain=1
									elif "11" in reading:
										gain=10
									elif "21" in reading:
										gain=100
									break
								if ("4095" in line):  
									value="0"
								elif ("4094" in line):
									value="0.01"
								else:
									value=int(line.strip())
									value=value/(2*float(gain))
									value= round(value, 3)#convert to resistance values
								if (x%2!=0):#Zigzag mode
									if (pt==0):
										matrix1[19-y][x]=value
									elif(pt==1):
										matrix50[19-y][2*x+1]=value
									elif(pt==2):
										matrix50[19-y][2*x]=value
								else:
									if (pt==0):
										matrix1[y][x]=value
									elif(pt==1):
										matrix50[y][2*x]=value
									elif(pt==2):
										matrix50[y][2*x+1]=value
							self.dlgImport.progressBar.setValue((100/cols)*(x+1))
							app.processEvents()
				
				### Rotate 
				
					if self.dlgImport.SWV.isChecked():
						matrix1=np.flipud(matrix1)
					elif self.dlgImport.SWH.isChecked():
						matrix1=np.rot90(matrix1)
						
					elif self.dlgImport.SEV.isChecked():
						matrix1=np.rot90(matrix1,2)

					elif self.dlgImport.SEH.isChecked():
						matrix1=np.rot90(matrix1,3)
						matrix1=np.flipud(matrix1)
						
					elif self.dlgImport.NWV.isChecked():
						pass
					elif self.dlgImport.NWH.isChecked():
						matrix1=np.rot90(matrix1)
						matrix1=np.flipud(matrix1)
						
					elif self.dlgImport.NEH.isChecked():
						matrix1=np.rot90(matrix1,3)
					elif self.dlgImport.NEV.isChecked():
						matrix1=np.fliplr(matrix1)

				#### Writing file. Checking whether the file already exists ####
					
					fname1='%s\%s_%s.csv' %(self.pathRaw,siteNameID,countStr)
					if (os.path.isfile(fname1)):
						msg=QMessageBox.about(self, "Error", "Error: Grid %s Already exists. Erase it first." %ii)
						break
					else:
						np.savetxt(fname1, matrix1, delimiter=",", fmt='%.2f')
					if mode==1:
						fname50='%s\grid50_%s.csv' %(self.pathRaw,countStr)
						if (os.path.isfile(fname1)):
							msg=QMessageBox.about(self, "Error", "Error: Grid %s Already exists. Erase it first." %ii)
							break
						else:
							matrix50=np.rot90(matrix50)
							np.savetxt(fname50, matrix50, delimiter=",", fmt='%.2f')
					app.processEvents()

				if (started==1 and bytesToRead==""):
					ser.flushInput()
					ser.flushOutput()
					ser.close()
					del ser
					self.dlgImport.status.setText("Done")
					self.dlgImport.go.setText("Done")
					self.dlgImport.close()
					
					break

			
			
	def saveParam(self):
		try:
			confFile=open(os.path.join(os.path.dirname(__file__), 'conf.txt'),'w')
		except:
			print ("Error opening the config file. Check you have the rights to write in the directory.")
		
		conftxt="SITEDIR="+ self.foldername + "\n"
		conftxt+="SITENAME="+ self.siteName + "\n"
		conftxt+="TILESIZEX=%s\n" %self.tileSize[0]
		conftxt+="TILESIZEY=%s\n" %self.tileSize[1]
		conftxt+="EPSG= %s\n" %self.epsg
		
		confFile.write(conftxt)
		
	def loadParam(self):
		confFile=open(os.path.join(os.path.dirname(__file__), 'conf.txt'),'r')

		# print "Error loading the config file. Default values will be used."
		##Set some default values
		X=20
		Y=20
		self.foldername=""
		for line in confFile:
			if "SITEDIR" in line:
				foldername=line.split('=')[1].strip()
				self.foldername=foldername
				self.pathRaw=foldername +"/raw/"
				self.pathOutput=foldername +"/output/"
				
				if (os.path.isdir(self.pathRaw)==0 or os.path.isdir(self.pathOutput)==0):
					self.actionImport_main.setEnabled(False)
					self.actionAssemble_main.setEnabled(False)
					self.dir_main.setText("")
					print("no dir found")
					self.foldername=""
				else:
					self.dir_main.setText(foldername)
					self.actionImport_main.setEnabled(True)
					self.actionAssemble_main.setEnabled(True)
					self.dir_main.setText(self.foldername)
					
			if "TILESIZEX" in line:
				X=int(line.split('=')[1])
			if "TILESIZEY" in line:
				Y=int(line.split('=')[1])
			if "SITENAME" in line:
				self.siteName=line.split('=')[1].strip()
				self.siteName_main.setText(self.siteName)
			if "EPSG" in line:
				self.epsg=line.split('=')[1].strip()
			
		self.tileSize=(X,Y)
		
				
	def process(self):
		self.clearInfo()
		self.index=self.getGeometry()
		self.mainMatrix=self.makeMosaic()
		self.exportGeoTiff_main.setEnabled(True)
		

	
	def matrix2figure(self, matrix):

		self.figure.clear()
		 
		if self.stdClip_check.isChecked():
			matrix=self.stdClip(matrix, self.stdClip_slider.value()/float(100))

		self.ax = self.figure.add_subplot(111)
		# discards the old graph
		#self.ax.hold(False)
		
		noData=0
		masked_data = np.ma.masked_where(matrix == noData, matrix)
		print (self.vis_palette.currentText())
		array = plt.imshow(masked_data, interpolation='none', cmap=str(self.vis_palette.currentText()))
		# cbar = plt.colorbar(mappable=array, orientation = 'horizontal', fraction=0.030, pad=0.07)
		# cbar.set_label('Resisitivity (Ohm/m)')
		plt.tight_layout()
		self.ax.grid(True)
		index=self.getGeometry()
		y=(index.shape[0])
		x=(index.shape[1])
		xmax=x*self.tileSize[0]
		ymax=y*self.tileSize[1]
		print(xmax,ymax)
		self.ax.xaxis.set_ticks(np.arange(0, xmax, 20))
		self.ax.yaxis.set_ticks(np.arange(0, ymax, 20))

		app.processEvents()

		self.canvas.draw()
		cid = self.canvas.mpl_connect('button_press_event', self.onclickFig)
		zo=self.canvas.mpl_connect('scroll_event',self.zoom_fun)
		cidMove=self.canvas.mpl_connect('motion_notify_event', self.on_motion)
		self.press=None
		cidRelease= self.canvas.mpl_connect('button_release_event', self.on_release)
		self.currentSelection=(-1,-1)
		
	def exportGeoTiff(self, filename, mat):
		import os.path
		import gdal, osr
		
		mat=np.int16(mat)
		
		xSize=mat.shape[1]
		ySize=mat.shape[0]
		step=1
		output_file=str(self.pathOutput+filename+'.tif')

		xCoord=0
		yCoord=0
		rotX=0
		rotY=0
		epsg=int(self.epsg)
		#epsg=32633 UTM nord 33
		#epsg=3004 Monte Mario 2
		print('Output coordintate system: %s' % epsg)
		geoTrans=[ xCoord, step , 0,  yCoord , 0, step ]
		srs = osr.SpatialReference()
		srs.ImportFromEPSG(epsg)
		# Create gtif (uncomment when using gdal)
		# 
		DataType= gdal.GDT_UInt16
		driver = gdal.GetDriverByName("GTiff")
		dst_ds = driver.Create(output_file, xSize, ySize, 1, DataType)
		#top left x, w-e pixel resolution, rotation, top left y, rotation, n-s pixel resolution
		print (geoTrans)
		#leavev the geotransform to use worldfile
		##dst_ds.SetGeoTransform( geoTrans )

		
		dst_ds.SetProjection( srs.ExportToWkt() )
		


		# write the band
		dst_ds.GetRasterBand(1).WriteArray(mat)
		band = dst_ds.GetRasterBand(1)
		band.SetNoDataValue(0)
		band.FlushCache()
	
	def exportTiff(self, filename, mat):
		import os.path
		import gdal, osr
		from libtiff import TIFF
		import arcpy
	
		
		mat=np.uint16(mat)
		
		xSize=mat.shape[1]
		ySize=mat.shape[0]
		step=1
		output_file=str(self.pathOutput+filename+'.tif')
		
		tiff = TIFF.open(output_file, mode='w')
		tiff.write_image(mat)
		tiff.close()
		
		arcpy.SetRasterProperties_management(output_file, "GENERIC","#" , "0" , "#")
	
	def georeferencing(self):
		import arcpy
		if os.path.isfile(self.pathOutput+"gcp.txt"):
			print ("Georeferencing output from GCPs")
			files=os.listdir(self.pathOutput)
			for file in files:
				if ".tif" in file:	
					try:
						arcpy.WarpFromFile_management(
						self.pathOutput+file, self.pathOutput+"georef_"+file,
						self.pathOutput+"gcp.txt", "POLYORDER1", "BILINEAR")
					except:
						print ("Error georeferencing "+file)
		else:
			print ("No GCP file found.")
	
	def normalize(self,mat):
		min=999999
		max=0
		for i in range (0,mat.shape[0]):
			for ii in range (0,mat.shape[1]):
				if (mat[i][ii]!=0 and mat[i][ii]<min):
					min=mat[i][ii]
				if (mat[i][ii]!=0 and mat[i][ii]>max):
					max=mat[i][ii]
		print(min, max)
		mat=((mat-min)/(max-min))
		return mat
		
	def normalizeClip(self,mat,clip):
		dev=mat.std()
		mean=mat.mean()
		min=mean-clip*dev
		max=mean+clip*dev
		
		mat=((mat-min)/(max-min))
		return mat
	
	def stdClip(self,mat,clip):
		dev=mat.std()
		mean=mat.mean()
		min=mean-clip*dev
		max=mean+clip*dev
		
		for i in range (0, mat.shape[0]):
			for ii in range (0,mat.shape [1]):
				if mat[i][ii]>max:	
					mat[i][ii]=max
				if mat[i][ii]<min:
					mat[i][ii]=min
				
		return mat
		
		
	def getGeometry(self):
		#print (str(self.pathOutput)+'geometry.txt')
		index=np.genfromtxt(str(self.pathOutput)+'geometry.txt',dtype='str', delimiter="\t");
		return index;
	
	def excludeOdds(self,mat):			#Exclude weird values and 0's from the mean calculation
		mat=np.array(mat)
		mat=mat.flatten()
		mat=mat[np.nonzero(mat)]
		std=np.std(mat)
		mean=np.mean(mat)
		indexOdds=list()
		limMin=mean-2.5*std
		limMax=mean+2.5*std
		for i in range (0, len(mat)):
			if(mat[i] <limMin or mat[i]>limMax):
				indexOdds.append(i)
		mat=np.delete(mat,indexOdds)
		return mat;


	def delta_extrap(self,grid_2,adj_2):	#determine the difference between adajcent edges of two grids
		grid_extrap=np.zeros(grid_2.shape[0])
		adj_extrap=np.zeros(grid_2.shape[0])
		grid_lin=grid_2[:,0]
		adj_lin=adj_2[:,1]
		delete=[]
		good=0
		bad=0
		for i in range (0,len(grid_extrap)):
			grid_extrap[i]=((grid_2[i][0]-grid_2[i][1])*0.5)+grid_2[i][0]
			adj_extrap[i]=((adj_2[i][1]-adj_2[i][0])*0.5)+adj_2[i][1]
			
		diff=np.zeros(len(grid_extrap))
		
		for i in range (0,len(grid_extrap)):
			diff[i]=((grid_extrap[i]-adj_extrap[i])+(grid_lin[i]-adj_lin[i]))/2
			
		mean_diff=np.mean(diff)
		std_diff=np.std(diff)
		for i in range (0,len(diff)):
			if (grid_2[i][0]==0 or grid_2[i][1]==0 or adj_2[i][0]==0 or adj_2[i][1]==0):
				delete=np.append(delete,i)
			if (diff[i]>mean_diff+2*std_diff or diff[i]<mean_diff-2*std_diff):
				delete=np.append(delete,i)
				
		diff=np.delete(diff,delete)		
		if (len(diff)>2):#if the edge is not too small....
			d=np.round(np.mean(diff),3)			#the difference between the grids
			if (d!=0):
				w=np.power(len(diff),2)/(np.std(diff))	#The weighting factor
				good+=1
			else:
				w=0
				bad+=1
		else:
			w=0
			d=0
			bad+=1

		return d,w

	def edgeMatch2(self,matrix,sizeEdge):
		print ('edge matching...')
		edgeSize=sizeEdge
		
		#Split the whole matrix in tiles (grids of 20x20 in our case)
		xGrids=int(matrix.shape[1]/edgeSize)	
		yGrids=int(matrix.shape[0]/edgeSize)
		n=int(xGrids*yGrids)
		print (n)
		print (int(n))
		A=np.zeros([n,n])
		x=np.zeros([n])
		b=np.zeros([n])
		
		minInit=np.min(matrix)
		if minInit<0:
			print ("warning: Negative values in the data. This may cause errors later.\n Consider despiking or correct these data.")
			matSorted=np.sort(matrix, axis=None)
			pos=1
			for i in range (0,len(matSorted)):
				if matSorted[i]==0 and pos:
					print ("%s negative values" %(i))
					print (matSorted[0:i])
					pos=0
				if matSorted[i]>0.01:
					minInit=matSorted[i]
					break
		i=0
		maxInit=np.max(matrix)
		print (minInit,maxInit)
		range_init=maxInit-minInit
		bestW=0
		reference=0
		print ('%s rows x %s cols' %(yGrids,xGrids))
		for x in range(0,xGrids):
			for y in range (0,yGrids):	#for each grid we compute the mismatch d and the weight coefficient w with the four neighbours 1:W, 2:N, 3,E, 4S 
				ymin=y*edgeSize
				ymax=(y+1)*edgeSize
				xmin=x*edgeSize
				xmax=(x+1)*edgeSize
				#Adjacent edge
				if (x>0):
					gridW=(matrix[ymin:ymax,xmin:xmin+2])
					edgeW=(matrix[ymin:ymax,xmin-2:xmin])
					di1,wi1=self.delta_extrap(gridW,edgeW)
					

				else:
					di1=0
					wi1=0

				if (y<yGrids-1):	
					
					gridN=np.fliplr(np.rot90((matrix[ymax-2:ymax,xmin:xmax])))
					edgeN=np.fliplr(np.rot90((matrix[ymax:ymax+2,xmin:xmax])))
					di2,wi2=self.delta_extrap(gridN,edgeN)
				
				else:
					di2=0
					wi2=0
				
				if (x<xGrids-1):	
					gridE=np.fliplr((matrix[ymin:ymax,xmax-2:xmax]))
					edgeE=np.fliplr((matrix[ymin:ymax,xmax:xmax+2]))
					di3,wi3=self.delta_extrap(gridE,edgeE)
						
				else:
					di3=0
					wi3=0
					
				if (y>0):
					gridS=np.flipud(np.rot90((matrix[ymin:ymin+2,xmin:xmax])))
					edgeS=np.flipud(np.rot90((matrix[ymin-2:ymin,xmin:xmax])))
					di4,wi4=self.delta_extrap(gridS,edgeS)
					

				else:
					di4=0
					wi4=0
					
				if (wi1!=0 and wi2!=0 and wi3!=0 and wi4!=0):
					fitness=wi1+wi2+wi3+wi4
					if fitness>bestW:
						bestW=fitness
						bestGrid=(x,y)
						reference=1
				
				#following the equation of Haigh 1995
				A[i,i]=(wi1+wi2+wi3+wi4)				#factor of xi
				
				if (x>0):						#the left line has no W side
					A[i,i-yGrids]=-wi1				#factor of xi1
				if (y<yGrids-1):					#the top line has no N side
					A[i,i+1]=-wi2				#factor of xi2
				if (x<xGrids-1):					#the right line has no E side
					A[i,i+yGrids]=-wi3				#factor of xi3
				if (y>0):					#the bottom line has no S side
					A[i,i-1]=-wi4				#factor of xi4
				
				b[i]=((di1*wi1)+(di2*wi2)+(di3*wi3)+(di4*wi4))

				i+=1

		print ('Resolving the equation of the meaning of life...')
		try:
			U,s,V = np.linalg.svd(A) # SVD decomposition of A

			# computing the inverse using pinv
			pinv = np.linalg.pinv(A)
			# computing the inverse using the SVD decomposition
			pinv_svd = np.dot(np.dot(V.T,np.linalg.inv(np.diag(s))),U.T)
			
			c = np.dot(U.T,b) # c = U^t*b
			w = np.linalg.solve(np.diag(s),c) # w = V^t*c
			xSVD = np.dot(V.T,w) # x = V*w
			
			#the function is described here: http://students.mimuw.edu.pl/~pbechler/numpy_doc/reference/generated/numpy.linalg.lstsq.html
			corr=np.flipud(np.rot90(np.reshape(xSVD,(xGrids,yGrids)),1))	#We reshape the coefficient to the size of the initial matrix
		except: 
			errorMessage= 'Singular Matrix, edge matching equation could not be solved. Survey area is possibly too small.'
			print (errorMessage)
			QMessageBox.about(self, "Edge matching Error", errorMessage)
			return matrix
		else: 	
			#rescale to the reference grid:
			if reference:
				delta=corr[bestGrid[1]][bestGrid[0]]
				print ("reference grid at x:%s y:%s  delta:%s" % (bestGrid[0],bestGrid[1],delta))
				corr=corr-delta
			#apply the correction:
			matrix_out=np.zeros((matrix.shape[0],matrix.shape[1]))
			mask=np.zeros((matrix.shape[0],matrix.shape[1]))
			mask[matrix.nonzero()]=1
			for x in range(0,xGrids):
				for y in range (0,yGrids):
					ymin=y*edgeSize
					ymax=(y+1)*edgeSize
					xmin=x*edgeSize
					xmax=(x+1)*edgeSize
					
					b=corr[y,x]
					matrix_out[ymin:ymax,xmin:xmax]=matrix[ymin:ymax,xmin:xmax]-b
			
			matrix_out= matrix_out * mask
			min=np.nanmin(matrix_out)
			max=np.nanmax(matrix_out)
			range_output=max-min
			print (range_output)
			print (min)
			print (max)
			if (min<0):
				matrix_out=matrix_out-min

			print("minimum:%s"%(np.nanmin(matrix_out[matrix_out>0.0])))
			matrix_out=((matrix_out+minInit)/range_output)*maxInit
			matrix_mask= matrix_out * mask
			print("minimum:%s"%(np.nanmin(matrix_mask[matrix_out>0.0])))
			print("maximum:%s"%(np.nanmax(matrix_mask)))
			
			return matrix_mask
			
		
	def deslope(self,matrix,sizeEdge):
	
		print ("deloping...")
		edgeSize=sizeEdge
		
		#Split the whole matrix in tiles (grids of 20x20 in our case)
		xGrids=int(matrix.shape[1]/edgeSize)		
		yGrids=int(matrix.shape[0]/edgeSize)
		n=int(xGrids*yGrids)
		for x in range(0,xGrids):
			for y in range (0,yGrids):	#for each grid we compute the mismatch d and the weight coefficient w with the four neighbours 1:W, 2:N, 3,E, 4S 
				for a in range (0,(edgeSize-1)):
					xmin=x*edgeSize
					xmax=(x+1)*edgeSize
					yline=y*edgeSize+a
					
					lineBottom=matrix[yline,xmin:xmax]
					lineTop=matrix[yline+1,xmin:xmax]
					
					delta=np.mean(lineTop)-np.mean(lineBottom)
					matrix[yline+1,xmin:xmax]=lineTop-delta
					
					
		
		return matrix 
	
	def gaussian_blur1d(self, in_array, size):
		#check validity
		try:
			if 0 in in_array.shape:
				raise Exception("Null array can't be processed!")
		except TypeError:
			raise Exception("Null array can't be processed!")
		# expand in_array to fit edge of kernel
		padded_array = np.pad(in_array, size, 'symmetric').astype(float)
		# build kernel
		x, y = np.mgrid[-size:size + 1, -size:size + 1]
		g = np.exp(-(x**2 / float(size) + y**2 / float(size)))
		g = (g / g.sum()).astype(float)
		# do the Gaussian blur
		out_array = fftconvolve(padded_array, g, mode='valid')
		return out_array.astype(in_array.dtype)
	
	def sharpening(self, in_array, alpha):
		try:
			if 0 in in_array.shape:
				raise Exception("Null array can't be processed!")
		except TypeError:
			raise Exception("Null array can't be processed!")
		f=in_array
		blurred_f = ndimage.gaussian_filter(f, 3)

		filter_blurred_f = ndimage.gaussian_filter(blurred_f, 1)

		alpha = 30
		sharpened = blurred_f + alpha * (blurred_f - filter_blurred_f)
		
		return sharpened.astype(in_array.dtype)
		
	def makeMosaic(self):
		from PIL import Image
		self.addInfo("Load parameters\n")
		self.siteName=self.siteName_main.text()
		gridSize=self.gridSize
		index=self.getGeometry()
		zero=np.zeros(gridSize)
		x=index.shape[0]
		y=index.shape[1]
		self.addInfo("Assembling tiles\n")
		for i in range (0,x):
			for ii in range (0,y):
				
				if (index[i][ii]=='0'):
					A=zero
				else:
					try:
						A = np.genfromtxt(str(self.pathRaw+self.siteName+'_'+index[i][ii]+'.csv'), delimiter=",")
					except:
						print ('Warning: Grid '+index[i][ii]+'  not found.\n'+str(self.pathRaw+self.siteName+'_'+index[i][ii]+'.csv'))
						A=zero
					if A.shape!=(20,20):
						print ("grid of odd dimensions: " + index[i][ii] )
						print (A.shape)
				if (ii==0):
					line=A
				else:
					#print('--------Grid: %s - %s -------' %(i, ii))
					grid=A
					#grid=edgeMatch(line,A,'horizontal')
					line=np.concatenate((line,grid),axis=1)
					
			if (i==0):
				mos=line
			else:
				#line=edgeMatch(mos,line,'vertical')
				mos=np.concatenate((mos,line),axis=0)
				
		if (self.despike_main.isChecked()):
			self.addInfo("Despiking...")
			mos=p.despike(mos)
			self.addInfo("Done\n")
			
		if (self.deslope_main.isChecked()):
			self.addInfo("Desloping...")
			mos= self.deslope(mos,20)
			self.addInfo("Done\n")
		
		if (self.edgeMatching_main.isChecked()):
			self.addInfo("Edge matching...")
			mos=self.edgeMatch2(mos,20)
			self.addInfo("Done\n")
		
			
		#mos=localVariation(mos)
		step=1
		xtif=y*gridSize[0]
		ytif=x*gridSize[1]
		self.addInfo("Creating preview...")
		#mos,cdf = histeq(mos)
		print(np.min(mos),np.max(mos))
		print('%s x %s' %(x,y))
		hs_array = p.hillshade(mos,45, 315, 0.0025)
		self.makePreview(mos, hs_array, str(self.siteName))
		self.addInfo("Finished\n")
		self.matrix2figure(mos)
		return mos
		
	def makePreview(self,array, hillshade_mat, filename):
		import matplotlib
		import matplotlib.mlab as mlab
		import matplotlib.pyplot as plt
		import matplotlib.cm as cm
		from PIL import Image
		import cv2
		#import scipy.ndimage
		x=array.shape[0]
		y=array.shape[1]
		min= 99999
		max=0
		if self.stdClip_check.isChecked():
				array=self.stdClip(array, self.stdClip_slider.value()/float(100))
		for i in range (0,x):
			for ii in range (0,y):
				if (array[i][ii]!=0 and array[i][ii]<min):
					min=array[i][ii]
				if (array[i][ii]!=0 and array[i][ii]>max):
					max=array[i][ii]
		print('min: %.2f max: %.2f \nsize: %s x %s' %(min,max, x, y))
	

		mask=np.empty([x, y], dtype='float64')
		for i in range (0,x):
			for ii in range (0,y):
				if (array[i][ii]!=0):
					mask[i][ii]=255
				if (array[i][ii]==0):
					mask[i][ii]=0

		if (min!=max and max!=0):
			
			array=(1-(array-min)/(max-min))
			array = cv2.resize(array, (0,0), fx=5, fy=5) 
			hillshade_mat = cv2.resize(hillshade_mat, (0,0), fx=5, fy=5) 
			mask = cv2.resize(mask, (0,0), fx=5, fy=5,  interpolation=cv2.INTER_NEAREST) 
			#array= scipy.ndimage.median_filter(array, 4)	
			values = Image.fromarray(np.uint8(cm.jet_r(array)*255)).convert('RGB')
			 
			
			
				
			hs_array = Image.fromarray(np.uint8(hillshade_mat)).convert('RGB')
			new_img = Image.blend(values, hs_array, 0.3).convert('RGBA')
			mask = Image.fromarray(np.uint8(mask)).convert('L')
			new_img.putalpha(mask)
			new_img.save(str(self.pathOutput+filename)+'preview.png')
			# self.displayPreview()
		else:
			print('error in reading image')

	
	def exportGeo(self):

		print('Export image...')
		self.statusBar().showMessage('Export image...')
		self.exportGeoTiff(self.siteName, self.mainMatrix*100)
		print('Export hillshade...')
		self.statusBar().showMessage('Export hillshade...')
		hs_array = p.hillshade(self.mainMatrix*100,45, 315, 0.0025)
		self.exportGeoTiff(self.siteName+"_hs", hs_array)
		self.statusBar().showMessage('GeoTIFF exported')
		# self.georeferencing()
		
if __name__ == "__main__":
	app = QApplication(sys.argv)
	p=Process()
	w = MyApp()
	
	w.show()
	sys.exit(app.exec_())
