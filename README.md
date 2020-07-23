# GeoResistivity Processing Manual

## Warning
This piece of software is distributed as is. It has been written as a Python script and therefore many functionalities are to be adjusted from the code itself. Everyone is highly encouraged to copy, improve and redistribute any part of the code that may be useful. 
The functionamlity of the GUI program may be limited to the use made of it (size of the grids is fixed, coordinate system list limited, etc.). All of this can be easily modified from the code itself.

This being said, the script should be able to run relatively smooth and allow to download data from a RM85 and export the data to a GeoTIFF file.

## Installation

The programm is a distributed as a Python script. You need to have Python (3.4 or 2.7) installed on your computer (installed if you have ArcGIS).
There are dependencies to install separatelly:
- GDAL
- PyQt 5
- Numpy
- Matplotlib
- Serial

It can be done by executing the command:
pip install numpy matplotlib serial

For GDAL, you may have to follow this tutorial. If you have QGIS you will have a possibly a different version.


They are common packages, check on Google how to have them installed on your machine.

## Usage
To run the script open the cmd terminal in windows and type <br/>
"cd /the/path/to/the/file"
`"python GeoUI.py"`<br/>
The windows will open, but you will stil have the terminal to find out about errors (nothing is perfect).


### Create new survey
To start with a new survey, you need to create a repertory with the following structure:

-SITENAME/ <br/>
&nbsp;&nbsp;&nbsp;&nbsp;+output/<br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-geometry.txt<br/>
&nbsp;&nbsp;&nbsp;&nbsp;+raw/<br/>

### Select the current site
In the space top left, select the directory of the site you work on wich contains the above mentionned folders. If it doesn't you will get an error message.

### Download data
To download data go to `File` > `Import from RM85`
  - select the number of the first grid you will download (it should be automatically the right one).
  - select the size of your grid (20 by 20)
  - select the port of the device
  - keep the baudrate at 9600
  - select the corner of the grid you used the most that day (you can still turn and flip everything around later, but it will save you time to have most of them all right)
  
###  Assemble grids

The grid assemblage is done automatically following the file "geometry.txt" in te repertory "output/".

The file can be edited from `File` > `Assemble grid`. It is a simple tab separated table which has to be of complete lines and collums. 
Empty grids are marked with "0".

Example:

```0   01  02  0
03  04  05  0
06  09  10  12
0   07  08  0
```


Incorrect (All the lines must be the same length!):

```0   01  02 
03  04  05  
06  09  10  12
0  07  08  
```

###  Process

Once loaded each grid can be rotated or mirrored from the interface: Press `Go` and use the buttons on the top left corner of the visualization window.


## Desctiption of lagorythms

### Despike
Despike option is supposed to remove the noise in the data (misreadings as they occur alwys in teh field). Try with and without and see what's best. Some values are not depiked, then you need to correct them manually: right click on the grid -> `Open grid in editor`.
You have to manually average the surrounding values of the odd point.

### Edge Matching
This important function allows you to not calibrate the remote probes in the field. They only need to be more than 20m away from your current grid. The spacing of teh electrodes does not really matters, but using most of the avilable cable is a safe way to place them (about 2m apart).
Thicking this option will remove teh tile effect due to different moiture condition (on surveys conducted on several days) and that occur when you move the remote electrodes.

### Data previsualization
These function are quite limited as you are expected to visualize the data in a GIS environement later. You can however previsualise the data with two contrast adjustement options: min-max and standart deviation.

### Export
You can export your data as a GeoTiff file already with a coordinate system (but not georeferenced). You can select the coordinate system in `Edit` > `Settings`.

