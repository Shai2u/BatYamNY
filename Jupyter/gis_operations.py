import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import folium
from IPython.display import HTML, display

class GIS_operations:
        #this class will help with simple mapping operations
    
    @staticmethod
    def DisplayMap(filePath):
        try:
            geoData = gpd.read_file(filePath, driver="ESRI Shapefile")
            # Plot polygons in light grey
            gpd.plotting.plot_dataframe(geoData, facecolor='grey',  linewidth=1)

        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")
        finally:
            print("file Closed")

        #this class will help with simple mapping operations
    
    @staticmethod
    
    def saveToGeoPackageLayer(whereToSave,layer, geodata):
        try:
            geodata.to_file(whereToSave, layer=layer, driver="GPKG")
            # Plot polygons in light grey

        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")
        finally:
            print("file Closed")

    @staticmethod
    def createWebMap(feature):
        #displahs the layer in a webview
        try:
            if (feature.crs['init'] == 'epsg:2039'):
        
                #feature_inter = feature.to_crs("+proj=tmerc +lat_0=31.7343936111111 +lon_0=35.2045169444445 +k=1.0000067 +x_0=219529.584 +y_0=626907.39 +ellps=GRS80 +towgs84=-23.772,-17.490,-17.859,-0.31320,-1.85274,1.67299,5.4262 +units=m +no_defs")
                #crs_4326 =  {'init': 'epsg:4326'}
                #feature_wgs_84 = feature_inter.to_crs(crs_4326)
                feature_wgs_84 = GIS_operations.Convert_2039_2_4326(feature)
            elif (feature.crs['init'] == 'epsg:6991' or feature.crs['init'] == 'epsg:6984'):
                #crs_4326 =  {'init': 'epsg:4326'}
                feature_wgs_84 = GIS_operations.Convert_6991_2_4326(feature)
            else:
                feature_wgs_84 = feature

            mapa = folium.Map([32.025, 34.745],
                  zoom_start=16,
                  tiles='cartodbpositron')
            gjson = feature_wgs_84.to_json()
            folium.GeoJson(
                gjson,
                name='geojson'
                ).add_to(mapa)
            folium.LayerControl().add_to(mapa)
            display(mapa)
        except Exception as e:
            print(e)
        else:
            print("Mapping creation successful")
        finally:
            mapa

    


    @staticmethod
    def Convert_2039_2_4326(feature):
        #Convert From ESPG 2039 (Israel TM Grid) to ESPG 4326 (WGS 84)
        try:
            #step 1 
            interFeature = feature.to_crs("+proj=tmerc +lat_0=31.7343936111111 +lon_0=35.2045169444445 +k=1.0000067 +x_0=219529.584 +y_0=626907.39 +ellps=GRS80 +towgs84=-23.772,-17.490,-17.859,-0.31320,-1.85274,1.67299,5.4262 +units=m +no_defs")
            crs_4326 =  {'init': 'epsg:4326'}
            #step 2
            Feature_4326 = interFeature.to_crs(crs_4326)
            return (Feature_4326)

        except Exception as e:
            print(e)
        else:
            print("Conversion to WGS 84 Successful")
    
    @staticmethod
    def Convert_4326_2_2039(feature):
        #Convert From ESPG 4326 (WGS 84) To ESPG 2039 (Israel TM Grid)
        try:
            #step 1 
            interFeature = feature.to_crs("+proj=tmerc +lat_0=31.7343936111111 +lon_0=35.2045169444445 +k=1.0000067 +x_0=219529.584 +y_0=626907.39 +ellps=GRS80 +towgs84=-23.772,-17.490,-17.859,-0.31320,-1.85274,1.67299,5.4262 +units=m +no_defs")
            crs_2039 =  {'init': 'epsg:2039'}
            #step 2
            Feature_2039 = interFeature.to_crs(crs_2039)
            return (Feature_2039)
            
        except Exception as e:
            print(e)
        else:
            print("Conversion to Israel TM Grid Successful")

    
            

 
    @staticmethod
    def Convert_6991_2_4326(feature):
        #Convert From ESPG 2039 (Israel TM Grid) to ESPG 4326 (WGS 84)
        try:
            #step 1 
            crs_4326 =  {'init': 'epsg:4326'}
            Feature_4326 = feature.to_crs(crs_4326)
            return (Feature_4326)

        except Exception as e:
            print(e)
        else:
            print("Conversion to WGS 84 Successful")

    @staticmethod
    def Convert_4326_2_6991(feature):
        #Convert From ESPG 2039 (Israel TM Grid) to ESPG 4326 (WGS 84)
        try:
            #step 1 
            crs_6991 =  {'init': 'epsg:6991'}
            Feature_6991= feature.to_crs(crs_6991)
            return (Feature_6991)

        except Exception as e:
            print(e)
        else:
            print("Conversion to WGS 84 Successful")

    
    @staticmethod
    def Convert_4326_2_6991_with_intermediate(feature):
        #Convert From ESPG 2039 (Israel TM Grid) to ESPG 4326 (WGS 84)
        try:
            #step 1 
            interFeature = feature.to_crs("+proj=tmerc +lat_0=31.7343936111111 +lon_0=35.2045169444445 +k=1.0000067 +x_0=219529.584 +y_0=626907.39 +ellps=GRS80 +towgs84=-23.772,-17.490,-17.859,-0.31320,-1.85274,1.67299,5.4262 +units=m +no_defs")

            crs_6991 =  {'init': 'epsg:6991'}
            Feature_6991= interFeature.to_crs(crs_6991)
            return (Feature_6991)

        except Exception as e:
            print(e)
        else:
            print("Conversion to WGS 84 Successful")

    @staticmethod
    def get_wgs_84_point(newPoint):
        if (newPoint.crs['init'] == 'epsg:2039'):
        
            newPoint_wgs_84 = GIS_operations.Convert_2039_2_4326(newPoint)

        elif (newPoint.crs['init'] == 'epsg:6991' or newPoint.crs['init'] == 'epsg:6984'):
            #crs_4326 =  {'init': 'epsg:4326'}
            newPoint_wgs_84 = GIS_operations.Convert_6991_2_4326(newPoint)
        else:
            newPoint_wgs_84 = newPoint
        return newPoint_wgs_84

    @staticmethod
    def convert_list_2039_4326(newList):
        convrted_list = []
        for pair in newList:
            crs_2039 = {'init': 'epsg:2039'}          
            pts_2039 = gpd.GeoSeries(Point(pair[0],pair[1]),crs = crs_2039)
            pts_4326 = GIS_operations.Convert_2039_2_4326(pts_2039)
            newPair = [pts_4326.y[0],pts_4326.x[0]]
            convrted_list.append(newPair)
        return convrted_list

    @staticmethod
    def create_Point_From_array(arrayPoint, espg='2039'):
        crs = {'init': 'epsg:'+espg}
        pts = gpd.GeoSeries(Point(arrayPoint[0],arrayPoint[1]),crs = crs)
        return pts