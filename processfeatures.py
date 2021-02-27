"""
/***************************************************************************
 PointsToPaths
                                 A QGIS plugin
 Converts points to lines with vertices grouped by a text or integer field
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
from __future__ import print_function
from builtins import str
from builtins import range
from builtins import object
from PyQt5.QtCore import QVariant
from qgis.core import *
from datetime import datetime
from datetime import timedelta

class ProcessFeatures(object):

    def __init__(self, layer, fname, order_attr_name=None, order_attr_format=None, group_attr_name=None):
        self.layer = layer
        self.fname = fname
        self.order_attr = order_attr_name
        self.format_attr = order_attr_format
        self.group_attr = group_attr_name

    def generatePointDict(self):
        if not self.layer.isValid():
            # fix_print_with_import
            print("Layer failed to load!")
        else:
            QgsProject.instance().addMapLayer(self.layer)
            self.provider = self.layer.dataProvider()
            #self.feat = QgsFeature()
            self.features = self.layer.selectedFeatures()
            if len(self.features) == 0:
                self.features = self.provider.getFeatures()
            self.allAttrs = self.provider.attributeIndexes()
            self.feat_dict = {}
            self.order_attr_index = self.provider.fieldNameIndex(self.order_attr)
            self.group_attr_index = self.provider.fieldNameIndex(self.group_attr)
            for feat in self.features:
                self.geom = feat.geometry()
                self.coords = self.geom.asPoint()
                self.attrs = feat.attributes()
                self.order_attr_value = self.attrs[self.order_attr_index]
                self.group_attr_value = self.attrs[self.group_attr_index]
                for attr in self.attrs:
                    for conversion_fn in (
                            (lambda d: datetime.strptime(str(d), str(self.format_attr))),
                            (lambda d: float(d)),
                            (lambda d: d.toPyDateTime()),
                            (lambda d: d.toPyDate()),
                    ):
                        try:
                            self.order_value = conversion_fn(self.order_attr_value)
                            break
                        except:
                            pass
                    if not hasattr(self, 'order_value'):
                        raise ValueError('Order field is not an integer type or date format is invalid')
                    if attr == self.group_attr_value:
                        try:
                            self.feat_dict[attr].append((self.order_value, self.coords[0], self.coords[1]))
                        except:
                            self.feat_dict[attr] = [(self.order_value, self.coords[0], self.coords[1])]
        return self.feat_dict


    def findGaps(self, list_of_times, gap):
        self.arrays = []
        self.current_array = []
        try:
            list_of_times[0][0] + 0
            self.time_delta = gap
        except:
            if gap != None:
                self.time_delta = timedelta(minutes=gap)
        for i in range(len(list_of_times)):
            if gap != None:
                if i < len(list_of_times)-1:
                    self.current_time = list_of_times[i][0]
                    self.future_time = list_of_times[i + 1][0]
                    if self.future_time - self.current_time > self.time_delta:
                        self.current_array.append(list_of_times[i])
                        self.arrays.append(self.current_array)
                        self.current_array = []
                    else:
                        self.current_array.append(list_of_times[i])
                if self.future_time <= self.current_time + self.time_delta:
                    self.current_array.append(list_of_times[i])
            else:
                self.current_array.append(list_of_times[i])
        self.arrays.append(self.current_array)
        return self.arrays


    def writeShapefile(self, points_dict, crs, gap=None, linesPerVertex=None):
        fields = [
            QgsField("group", QVariant.String),
            QgsField("begin", QVariant.String),
            QgsField("end", QVariant.String)
        ]
        qgsfields = QgsFields()
        for field in fields:
            qgsfields.append(field)

        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.attributes = [0, 1, 2]
        save_options.driverName = 'ESRI Shapefile'
        save_options.fileEncoding = 'CP1250'
        writer = QgsVectorFileWriter.create(
            self.fname,
            qgsfields,
            QgsWkbTypes.LineString,
            crs,
            QgsCoordinateTransformContext(),
            save_options
        )

        for (ky, vals) in list(points_dict.items()):
            if len(vals) > 1:
                vals.sort()
                gapped_vals = self.findGaps(vals, gap)
                for val in gapped_vals:
                    if len(val) > 1:
                        val.sort()
                        if linesPerVertex == True:
                            for i, v in enumerate(val[:-1]):
                                feat = QgsFeature()
                                feat.setFields(qgsfields)
                                start = val[i]
                                end = val[i + 1]
                                if start[1] != end[1] and start[2] != end[2]:
                                    vertices = [QgsPoint(start[1], start[2]), QgsPoint(end[1], end[2])]
                                    feat.setGeometry(QgsGeometry.fromPolyline(vertices))
                                    feat.setAttributes([str(ky), str(start[0]), str(end[0])])
                                    writer.addFeature(feat)
                                    # features.append(feat)
                        else:
                            feat = QgsFeature()
                            feat.setFields(qgsfields)
                            vertices = []
                            for i in val:
                                vertices.append(QgsPoint(i[1], i[2]))
                            feat.setGeometry(QgsGeometry.fromPolyline(vertices))
                            feat.setAttributes([str(ky), str(val[0][0]), str(val[-1][0])])
                            writer.addFeature(feat)
        del writer
