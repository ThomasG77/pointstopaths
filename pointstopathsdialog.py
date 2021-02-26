"""
/***************************************************************************
 PointsToPaths
                                 A QGIS plugin
 Converts points to lines with verticies grouped by a text or integer field
 and ordered by an integer or date string field
                             -------------------
        begin                : 2011-08-02
        copyright            : (C) 2011 by Cyrus Hiatt
        email                : cyrusnhiatt@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
import os

from builtins import str
from qgis.PyQt import QtCore, QtGui, QtWidgets, uic
from .ui_pointstopaths import Ui_PointsToPaths
from .processfeatures import ProcessFeatures
from qgis.core import *
from qgis.gui import *

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'pointstopaths_dialog_base.ui'))

# adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
class PointsToPathsDialog(QtWidgets.QDialog,FORM_CLASS):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = FORM_CLASS()
        self.ui.setupUi(self)
        self.ui.btnBrowse.clicked.connect(self.outFile)
        self.ui.inShape.currentIndexChanged.connect(self.checkLayer)
        self.ui.inShape.currentIndexChanged.connect(self.update)
        self.manageGui()
        self.show()

    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def checkLayer(self):
        inputLayer = str( self.ui.inShape.currentText() )
        if inputLayer != "":
            changedLayer = getVectorLayerByName( inputLayer )

    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def update(self):
        self.ui.orderField.clear()
        self.ui.attrField.clear()
        inputLayer = str( self.ui.inShape.currentText() )
        if inputLayer != "":
            changedLayer = getVectorLayerByName( inputLayer )
            changedField = changedLayer.dataProvider().fields()
            for field in changedField:
                name = field.name()
                self.ui.orderField.addItem(name)
                self.ui.attrField.addItem(name)

    # Return list point layer names in QgsProject
    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def manageGui(self):
        myList = []
        self.ui.inShape.clear()
        myList = getLayerNames( [ QgsWkbTypes.Point ] )
        self.ui.inShape.addItems( myList )
        return

    # portions adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def accept(self):
        QtGui
        if self.ui.inShape.currentText() == "":
            QtGui.QMessageBox.warning( self, "PointsToPaths", self.tr( "Please specify an input layer" ) )
            return
        elif self.ui.attrField.currentText() == "":
            QtGui.QMessageBox.warning( self, "PointsToPaths", self.tr( "Please define specific input field" ) )
        elif self.ui.orderField.currentText() == "":
            QtGui.QMessageBox.warning( self, "PointsToPaths", self.tr( "Please define specific input field" ) )
        elif self.getOutFilePath() == "":
            QtGui.QMessageBox.warning( self, "PointsToPaths", self.tr( "Please specify output shapefile" ) )
        else:
            inputLayer = str( self.ui.inShape.currentText() )
            layer = getVectorLayerByName( inputLayer )
            provider = layer.dataProvider()
            processor = ProcessFeatures(layer, self.getOutFilePath(), self.ui.orderField.currentText(), self.getTimeFormat(), self.ui.attrField.currentText())
            points = processor.generatePointDict()
            processor.writeShapefile(points, layer.crs(), self.getGapPeriod(), self.getLinesPerVertex())
            message = str(self.tr('Created output shapefile:'))
            message = '\n'.join([message, str(self.getOutFilePath())])
            message = '\n'.join([message,str(self.tr('Would you like to add the new layer to the TOC?'))])
            addToTOC = QtGui.QMessageBox.question(self, "PointsToPaths", message,
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No, QtGui.QMessageBox.NoButton)
            if addToTOC == QtGui.QMessageBox.Yes:
                addShapeToCanvas(str(self.getOutFilePath()))


    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def outFile(self):
        outFilePath = saveDialog(self)
        if not outFilePath:
            return
        self.setOutFilePath(outFilePath)

    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def getOutFilePath(self):
        return self.ui.outShape.text()

    # adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
    def setOutFilePath(self, outFilePath):
        self.ui.outShape.setText(outFilePath)

    def getTimeFormat(self):
        return self.ui.dateFormat.text()

    def getGapPeriod(self):
        gap_string = self.ui.gapPeriod.text()
        if gap_string != '':
            try:
                gap = float(gap_string)
            except:
                raise ValueError('Gap period not a numeric value')
        else:
            gap = None
        return gap

    def getLinesPerVertex(self):
        is_checked = self.ui.linePerVertex.isChecked()
        return is_checked

# Return QgsVectorLayer from a layer name ( as string )
# adopted from 'fTools Plugin', Copyright (C) 2009  Carson Farmer
def getVectorLayerByName( myName ):
    layermap = QgsProject.instance().mapLayers()
    for name, layer in list(layermap.items()):
        if layer.type() == QgsMapLayer.VectorLayer and layer.name() == myName:
            if layer.isValid():
                return layer
            else:
                return None

# Return list of names of all layers in QgsProject
# adopted from 'fTools Plugin', Copyright (C) 2009  Carson Farmer
def getLayerNames( vTypes ):
    layermap = QgsProject.instance().mapLayers()
    layerlist = []
    if vTypes == "all":
        for name, layer in list(layermap.items()):
            layerlist.append( str( layer.name() ) )
    else:
        for name, layer in list(layermap.items()):
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.wkbType() in vTypes:
                    layerlist.append( str( layer.name() ) )
    return layerlist

# adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
def saveDialog(parent):
    settings = QtCore.QSettings()
    key = '/UI/lastShapefileDir'
    outDir = settings.value(key)
    filter = 'Shapefiles (*.shp)'
    outFilePath = QtGui.QFileDialog.getSaveFileName(parent, parent.tr('Save output shapefile'), outDir, filter)
    outFilePath = str(outFilePath)
    if outFilePath:
        root, ext = os.path.splitext(outFilePath)
        if ext.upper() != '.SHP':
            outFilePath = '%s.shp' % outFilePath
        outDir = os.path.dirname(outFilePath)
        settings.setValue(key, outDir)
    return outFilePath

# Convinience function to add a vector layer to canvas based on input shapefile path ( as string )
# adopted from 'fTools Plugin', Copyright (C) 2009  Carson Farmer
def addShapeToCanvas(shapeFilePath):
    layerName = os.path.basename(shapeFilePath)
    root, ext = os.path.splitext(layerName)
    if ext == '.shp':
        layerName = root
    vlayer_new = QgsVectorLayer(shapeFilePath, layerName, "ogr")
    if vlayer_new.isValid():
        QgsProject.instance().addMapLayer(vlayer_new)
        return True
    else:
        return False

# adopted from 'points2one', Copyright (C) 2010 Pavol Kapusta & Goyo Diaz
class FileDeletionError(Exception):
    pass
