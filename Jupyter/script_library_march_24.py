#from gis_local_webmap import GIS_local_webmap
#from gis_operations import GIS_operations
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
#from updateParcelAndBldg import updateParcels
#from agentGroups import AgentGroups


class script_library:


    def __init__(self):

        #self.geo_oldBldgs = gpd.read_file(script_library.oldBldgs['package'],layer=script_library.oldBldgs_renewal['layer'])
        #self.geo_oldBlockParcel = gpd.read_file(script_library.oldBlockParcel['package'],layer=script_library.oldBlockParcel['layer'])
        #self.geo_sample_building = gpd.read_file(script_library.newBldgs['package'],layer=script_library.newBldgs['sample_bldg'])
        #self.script = pd.read_excel(script_library.scriptFiles['parcelBldgScript'])
        #self.existing_bldgs = pd.read_excel(script_library.bldgs['Existing_buildings'])
        #self.hh = pd.read_excel(script_library.household['household'])
        #self.removedHH = pd.DataFrame()
        #self.iteration =0
        #self.AgentSet = AgentGroups()
        #self.oldBldgs = AgentGroups.groupDictionary["Group Age"][ageGroup]
        #self.newBldgs = AgentGroups.groupDictionary["Group Ownership"][ownerShip]
        #self.income = AgentGroups.groupDictionary["Group Income"][income]
        #self.scriptFiles = AgentGroups.groupDictionary["Group Nativity"][native]
    
    # def setIteration(self,i):
    #     self.iteration = i

    # def runIteration(self):
    #     i = self.iteration
    #     firstIteration = self.script.loc[i][['plan_num','Tam38Floor','Tama38Height','Units']]
    #     eb = self.existing_bldgs[['old_building_cost_vaad', 'original_units','purchase_p', 'rent_price', 'FuturePlanCode', 'bld_Id',
    #    'row_Num']]
    #     eb_1 = pd.merge(self.geo_oldBldgs,eb, left_on='rowNum',right_on='row_Num')
    #     current_update = eb_1[eb_1['FuturePlanCode']==str(firstIteration.plan_num)]
    #     #Update the fileds for the buildings
    #     current_update['floors']= firstIteration.Tam38Floor
    #     current_update['height']= firstIteration.Tama38Height
    #     current_update['newUnits']= firstIteration.Units #till I fix the duplicated units probelm1!!!
    #     current_update1= script_library.updatePrices(current_update,i)

    #     return current_update1
    #     #print(firstIteration)

    #     #print('test')

    # def getEssentialItems(self):
    #     currentLine = self.script.loc[self.iteration]

    #     nextPoint = [currentLine['EAST'],currentLine['NORTH']]
        
    #     floors = currentLine['Tam38Floor']

    #     units = currentLine['Units']
    #     return (nextPoint,floors,units)
    #     #units = currentLine['Units']
    #     #updateParcels.tama_38_operation(nextPoint,currentBldgs,sl.newBldgs['package'],toSaveRef,floors,units

    # @staticmethod   
    # def updatePrices(DF, iteration):
    #     #sl.oldBldgMeters
    #     #sl.tama38_addonMeter

    #     #case of Tama 38 only!!!!!

    #     sl = script_library
        
    #     metersOfBuilding =  sl.oldBldgMeters + sl.add_onSize['tama38'] # old and new size of hosue
    #     initalPrice = DF['rent_price']
    #     rent_price_increase = sl.rentalPriceIncrease(initalPrice,iteration)

    #     initla_value_price = DF['purchase_p']
    #     value_price_increase = sl.rentalPriceIncrease(initla_value_price,iteration)

    #     #value of property increase simulaiton
    #     DF['purchase_p'] = initla_value_price
    #     DF['unit_value'] = metersOfBuilding * initla_value_price

    #     #value of rent increase simulation
    #     DF['rent_price'] = rent_price_increase # price increase

    #     #other expenses
    #     DF['Arnona'] = metersOfBuilding*sl.ArnonaPriceMeter
    #     DF['Vaad'] = sl.vaadBait[8] # needed a function later

    #     #sum expenses according to Agent type
    #     DF['rent_expenses'] = metersOfBuilding*DF['rent_price'] +DF['Arnona'] + DF['Vaad']
    #     DF['own_expenses'] =  DF['Vaad'] + DF['Arnona']
    #     return DF

    # @staticmethod
    # def rentalPriceIncrease(initalPrice,iteration):
    #     #returns estimated price increase
    #     return initalPrice*1.1+0.01*iteration
