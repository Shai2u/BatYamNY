
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import folium
from IPython.display import HTML, display
from gis_operations import GIS_operations
class GIS_local_webmap:
    #This class deals with local webmaps
    layersNum = 0
    def __init__(self,latlng=[32.025, 34.745], zoom = 16):
           self.map = folium.Map(latlng,zoom_start=zoom,tiles='cartodbpositron')
           self.fillColor='#3399ff'
    
    def displayMap(self):
        try:   
           display(self.map)

        except Exception as e:
            print(e)
        else:
            print("Mapping Display successful")
    
    #This function will add a point to the map.
    def add2039_Point_array(self,newPoint,data='test', crsInput='2039',dis=True):
        #we assume all points are in 2039 and are in a list
        #create a new point
        crs = {'init': 'epsg:'+crsInput}
        pts = gpd.GeoSeries(Point(newPoint[0],newPoint[1]),crs = crs)
        try:
            wgs84_point = GIS_operations.get_wgs_84_point(pts)
            newPointArray = [wgs84_point.geometry.y[0],wgs84_point.geometry.x[0]]
            folium.Marker(location = newPointArray, popup=data,icon=folium.Icon(color='green')).add_to(self.map)
            if dis==True:
                display(self.map)
            else:
                pass
        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")

    #This function will add a point to the map.
    def add_point_as_marker(self,newPoint,crsInput='2039',dis=True):
        #we assume all points are in 2039 and are in a list
        #create a new point
        try:
            wgs84_point = GIS_operations.get_wgs_84_point(newPoint)
            newPointArray = [wgs84_point.geometry.y[0],wgs84_point.geometry.x[0]]
            folium.Marker(location = newPointArray, popup='test',icon=folium.Icon(color='green')).add_to(self.map)
            if dis==True:
                display(self.map)
            else:
                pass
        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")

    def add_points_asMarkers(self,PointsColumn,MarkerDataColumn):
        try:
            if (PointsColumn.crs['init'] == 'epsg:2039'):
                feature_wgs_84 = GIS_operations.Convert_2039_2_4326(PointsColumn)
            elif (PointsColumn.crs['init'] == 'epsg:6991' or PointsColumn.crs['init'] == 'epsg:6984'):
                #crs_4326 =  {'init': 'epsg:4326'}
                {'init': 'epsg:4326'}
                feature_wgs_84 = GIS_operations.Convert_6991_2_4326(PointsColumn)
            else:
                feature_wgs_84 = PointsColumn
            
            
            feature_wgs_84['lat'] = feature_wgs_84.geometry.y
            feature_wgs_84['lng'] = feature_wgs_84.geometry.x
            locations = feature_wgs_84[['lat','lng']]
            locationlist = locations.values.tolist()
            self.add4326_Points_array(locationlist,MarkerDataColumn)

        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")


    #This function will add many points to the map.
    def add4326_Points_array(self,newLis, labelData=[],dis=True):
        #we assume all points are in 4326 and are in a list
        if labelData==[]:
           labelData=['test' for x in range(0, len(newLis))]
        try:
            i=0
            for point in range(0, len(newLis)):
                folium.Marker(newLis[point], popup=str(i)+": "+labelData[i]).add_to(self.map)
                i= i + 1
            if dis==True:
                display(self.map)
            else:
                pass
        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")

    def addLayer(self,feature,colorF='blue', dis=True):
        try:
            if (feature.crs['init'] == 'epsg:2039'):
                feature_wgs_84 = GIS_operations.Convert_2039_2_4326(feature)
            elif (feature.crs['init'] == 'epsg:6991' or feature.crs['init'] == 'epsg:6984'):
                #crs_4326 =  {'init': 'epsg:4326'}
                {'init': 'epsg:4326'}
                feature_wgs_84 = GIS_operations.Convert_6991_2_4326(feature)
            else:
                feature_wgs_84 = feature
                print('in Else')

            gjson = feature_wgs_84.to_json()
            GIS_local_webmap.layersNum = GIS_local_webmap.layersNum + 1
            if (colorF=='blue'):
                folium.GeoJson(
                    gjson,
                    name='geojson'+str(GIS_local_webmap.layersNum),
                    style_function = GIS_local_webmap.style_functionBLUE
                    ).add_to(self.map)

            elif (colorF=='red'):
                folium.GeoJson(
                    gjson,
                    name='geojson'+str(GIS_local_webmap.layersNum),
                    style_function = GIS_local_webmap.style_functionRED
                    ).add_to(self.map)
            elif (colorF=='lightRed'):
                 folium.GeoJson(
                    gjson,
                    name='geojson'+str(GIS_local_webmap.layersNum),
                    style_function = GIS_local_webmap.style_functionLightRed
                    ).add_to(self.map)
            elif (colorF=='parcel'):
                style_1 ={'fillOpacity': 0.5,'weight': 1
                ,'fillColor': '##ffcccc'}
  
                folium.GeoJson(
                    gjson,
                    style_function = lambda x: style_1,
                    tooltip=folium.GeoJsonTooltip(fields=['GUSH_NUM','PARCEL'],aliases=['Block:','Parcel:'])
                    ).add_to(self.map)

            elif (colorF=='bldg'):
                style_1 ={'fillOpacity': 0.5,'weight': 1
                ,'fillColor': '##cc0000'}
  
                folium.GeoJson(
                    gjson,
                    style_function = lambda x: style_1,
                    tooltip=folium.GeoJsonTooltip(fields=['bld_id'],aliases=['Bld ID:'])
                    ).add_to(self.map) 
            else:
                folium.GeoJson(
                    gjson,
                    name='geojson'+str(GIS_local_webmap.layersNum),
                    style_function = GIS_local_webmap.style_functionLightGray
                    ).add_to(self.map)                  
            #folium.LayerControl().add_to(self.map)
            if dis:
                display(self.map)
        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")
        
    @staticmethod
    def style_functionBLUE(feature):
        #feature.plot()
        return {
            'fillOpacity': 0.5,
            'weight': 0.1,
            'fillColor': '#3399ff'
        }

    @staticmethod
    def style_functionRED(feature):
        #feature.plot()
        return {
            'fillOpacity': 0.5,
            'weight': 0.1,
            'fillColor': '#cc0000'
        }
    
    @staticmethod
    def style_functionLightGray(feature):
        #feature.plot()
        return {
            'fillOpacity': 0.3,
            'weight': 1,
            'fillColor': '##f3f1ff'
        }

    @staticmethod
    def style_functionLightRed(feature):
        #feature.plot()
        return {
            'fillOpacity': 0.5,
            'weight': 0.5,
            'fillColor': '##ffcccc'
        }