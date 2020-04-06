import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
import json
import os
import ipywidgets as widgets
from datetime import datetime
from datetime import date
from IPython.display import HTML, display

#Postgres
import psycopg2  # (if it is postgres/postgis)

class SSI:

    def __init__(self):
        #reference dictionary file
        #----------------------Loading Library and rule files
        path_1 = 'library_march_28.json'
        with open(path_1) as json_file:
            self.library = json.load(json_file)
        #print_library = json.dumps(self.library, indent=2)

        #rules dictionary file file
        path_2 = 'rules.json'
        with open(path_2) as json_file:
            self.rules = json.load(json_file)

        ##-------------setup widgets-----------------------
        
        self.simulation_folder = widgets.Text(
            value='cim_0326_1234',
            description='Folder:'
            )

        ## File name of agents
        self.agents_name = widgets.Text(
            value='agents.xlsx',
            description = 'Agent File'
            )
        
        dt = datetime.now()
        d1 = dt.strftime("%m%d_%H%M")
        sim_name="agents_cim_"+d1
        self.simulation_name = widgets.Text(
            value=sim_name,
            description='Simulation Name'
            )
        #displays map before
        self.before_map = widgets.Checkbox(
            value=False,
            description='Display Before Map?',
            disabled=False,
            indent=False
            )
        
        #displays map before
        self.AutoNameSimulation = widgets.Checkbox(
            value=False,
            description='Auto Name Simulation?',
            disabled=False,
            indent=False
            )
        self.infoText = widgets.Textarea(
            value='',
            placeholder='',
            description='',
            disabled=False
            )
   
    #This function Loads the Old Bldgs, backgrodund bldgs and the updated buildings
    def init_gis(self):
        pack_old_bldg = self.library["GIS_package"]["old_bldgs"]["package"]
        layer_old_bldg = self.library["GIS_package"]["old_bldgs"]["layer"]
        pack_all_old_bldg = self.library["GIS_package"]["old_bldgs_background"]["package"]
        layer_all_old_bldg = self.library["GIS_package"]["old_bldgs_background"]["layer"]
        pack_updated_bldg = self.library["GIS_package"]["updated_bldg"]["package"]
        layer_updated_bldg = self.library["GIS_package"]["updated_bldg"]["layer"]
        self.old_bldgs = gpd.read_file(pack_old_bldg,layer = layer_old_bldg,driver='GPKG')
        self.old_bg_bldgs = gpd.read_file(pack_all_old_bldg,layer = layer_all_old_bldg,driver='GPKG')
        self.updated_bldgs = gpd.read_file(pack_updated_bldg,layer = layer_updated_bldg,driver='GPKG')

    #This function Loads the master script files
    def init_db(self):
        self.sim_folder='simulationID/'+self.simulation_folder.value+'/'
        script_path = self.sim_folder+self.library["script_file"]
        #master script
        self.script_file = pd.read_excel(script_path)

        path_to_agents = self.sim_folder+ self.agents_name.value
        self.agent_ref = pd.read_excel(path_to_agents)
        self.bldg_path = self.sim_folder + self.library['bldg_path']
        
        #Before and after buildings
        before_n_after_path = self.sim_folder+self.library['before_n_after']
        self.bna = pd.read_excel(before_n_after_path)
        self.bna.reset_index(inplace=True, drop=True)

        l_op = len(self.script_file.index)
        self.itr_slider = widgets.IntSlider(
            min=0, max =l_op
            )    
    
    #This function displays the the original buildings Using Folium and displaying statistics to them
    def prepare_old_bldgs_map(self):
        ## TO DO need to prepare a new "Old Buildings" Excel file that lists the layers that are currently ready in the GIS with all the Data
        old_bldg_path = self.sim_folder + self.library['old_building_ref']
        bldg_list = pd.read_excel(old_bldg_path) ## Need to create a GIS file Generator to the files that are ready for production.

        select_bldg = self.old_bldgs['bld_id'].isin(bldg_list.bld_address)
        select_bldg_ds = self.old_bldgs[select_bldg][['bld_id','geometry']]
        select_bldg_ds.reset_index(inplace=True, drop=True)
        select_bldg_ds_join = pd.merge(select_bldg_ds,bldg_list,how='left',left_on='bld_id',right_on='bld_address')
        self.select_bldg_wgs_84 = SSI.Convert_2039_2_4326(select_bldg_ds_join)
        
        #get center point
        lon = self.select_bldg_wgs_84.geometry.centroid.x.mean()
        lat = self.select_bldg_wgs_84.geometry.centroid.y.mean()

        #add background buidling
        fmap = self.createNewMap(lat,lon)
        fmap = self.add2map_bldgs_to_renew(fmap)
        return(fmap)
    
    #Creates a map with Agents statistics T=0
    def prepare_agents_statistics_map_0(self):
        agent_mod = self.agent_mod_unpivot()
        agent_gb = agent_mod.groupby('AgentBldAdd')
        agents_stat = agent_gb.agg({'AgentIncome':'mean','AgentWealth':'mean','Age':'mean','Native_Seniority':'mean','Young':'count','Old':'count','Owner':'count','Rent':'count','Low Income':'count','Medium Income':'count','High Income':'count'})
        agents_stat.reset_index(inplace=True)
        agents_stat['AgentIncome'] = agents_stat['AgentIncome'].astype(int)
        agents_stat['AgentWealth'] = agents_stat['AgentWealth'].astype(int)
        agents_stat['Native_Seniority'] = agents_stat['Native_Seniority'].astype(int)
        agents_stat['Age'] = agents_stat['Age'].astype(int)
        select_bldg_slim = self.select_bldg_wgs_84[['geometry','bld_id']]
        bldg_with_agentStat = pd.merge(select_bldg_slim,agents_stat,how='left',left_on='bld_id',right_on='AgentBldAdd')
        fmap2 = self.createNewMap()
        fmap2 = self.add2map_agents_T0_stat(fmap2,bldg_with_agentStat)

        return fmap2

    #creates a map of Bat Yam with the background buildings
    def createNewMap(self , lat=32.02677, lon=34.74283):
        #initate map
        latlng=[lat, lon]
        zoom = 16
        fmap = folium.Map(latlng,zoom_start=zoom,tiles='cartodbpositron')
        
        old_all_bldgs_wgs84 = SSI.Convert_2039_2_4326(self.old_bg_bldgs)
        gjson = old_all_bldgs_wgs84.to_json()
        style_1 ={'fillOpacity': 0.25,'weight': 0,'fillColor': '##cc0000'}
        folium.GeoJson(gjson,
                    style_function = lambda x: style_1).add_to(fmap)
        return(fmap)

    #Adds to map the buildings to be renewed with the statisticsl data
    def add2map_bldgs_to_renew(self,fmap):
        gjson = self.select_bldg_wgs_84.to_json()
        style_2 ={'fillOpacity': 0.75,'weight': 1,'fillColor': '#ff0000'}
        folium.GeoJson(gjson,
                    style_function = lambda x: style_2,
                    tooltip=folium.GeoJsonTooltip(fields=['bld_address',
                                                            'Address Title',
                                                            'OriginalUnits',
                                                            'OriginalFloors',
                                                            'OriginalHouseSize',
                                                            'originalRentPercent',
                                                            'purchase_p',
                                                            'rent_price',
                                                            'Arnona',
                                                            'Old_Purchase', 
                                                            'OldRent',
                                                            'Tax and Maintenace'
                                                            ],
                                                    aliases=['Building Address Code:',
                                                            'Building Address:',
                                                            'Number of Units:',
                                                            'OriginalFloors:',
                                                            'Average house size:',
                                                            'Percent renters:',
                                                            'Price Per Meter:',
                                                            'Rent Per Meter:',
                                                            'Arnona:',
                                                            'Average Sell Price:', 
                                                            'Average Rent Price:',
                                                            'Tax and Maintenace:'                                                   
                                                            ])
                    ).add_to(fmap)
        return(fmap)
    
    def add2map_agents_T0_stat(self,fmap,bldg_with_agentStat):
        gjson = bldg_with_agentStat.to_json()
        style_3 ={'fillOpacity': 0.75,'weight': 1,'fillColor': '#ff0000'}
        folium.GeoJson(gjson,
                    style_function = lambda x: style_3,
                    tooltip=folium.GeoJsonTooltip(fields=['bld_id',
                                                            'AgentIncome',
                                                            'AgentWealth',
                                                            'Age',
                                                            'Native_Seniority',
                                                            'Young',
                                                            'Old',
                                                            'Owner',
                                                            'Rent',
                                                            'Low Income',
                                                            'Medium Income',
                                                            'High Income'
                                                            ],
                                                    aliases=['Building Address Code',
                                                            'Average Agent income',
                                                            'Average Agent Wealth',
                                                            'Average Age',
                                                            'Average Seniority in Neighborhood',
                                                            'Number of Young',
                                                            'Number of Old',
                                                            'Number of Owners',
                                                            'Number of Rent',
                                                            'Number of Low Income',
                                                            'Number of Medium Income',
                                                            'Number of High Income'                                                  
                                                            ])
                    ).add_to(fmap)
        return fmap

    def set_up_first_iteration(self):
        #copying the original Agents
        self.agent_0 = self.agent_ref.copy()
        #cleanup
        self.agent_0 = self.agent_0[['AgentAppUnit', 'AgentBldAdd', 'AgentIncome',
        'AgentWealth', 'AgentPurchaseThreshold', 'AgentRentThreshold', 'Age',
        'OwnerShip', 'AgeGroup', 'Native_Seniority', 'Native_Group', 'AgentID',
        'AgeGroupDesc', 'NativeDesc', 'OwnershipDesc', 'IncomeNum',
        'IncomeDesc']]
        #adding Threshold ability to stay for each agent and inital status
        self.agent_0 = self.updateAgentsThresholdData(self.agent_0,'staying')
        # creating a dateset for the excel files that will be saved
        #self.itr_agents_excel_ds = pd.DataFrame()
        #self.itr_bldg_excel_ds = pd.DataFrame()
        #self.itr_accumulated_bldg_excel_ds = pd.DataFrame()
        #self.itr_geokpackage_ds = pd.DataFrame()
        self.PopNum_forID = len(self.agent_0.index)

    
    #do one iteration
    def iterate(self):
        #get iteration number
        self.i = self.itr_slider.value
        i = self.i
        self.operation_pre_123(i)
        if (i==0):
            self.agent_i = self.agent_0.copy()

        if (self.typeOperation<3):
            
            self.infoText.value = self.infoText.value + "\n\n operation 1 or 2"
            self.operation_12()

        else:
            self.infoText.value = self.infoText.value + "\n\n operation 3"
            self.operation_3()
        self.operation_post_123(i)
        

    #run all iterations
    def iterateAll(self):
        l_op = len(self.script_file.index)
        for j in range(l_op):
            self.itr_slider.value = j
            self.iterate()
        self.saveAgentsExcel()
    
    #helper function pre operation for operations 12 and 3
    def operation_pre_123(self,i):
        self.infoText.value = self.infoText.value + "\n Iteration Number: " + str(i)
        # reference of the next row
        self.next_row = self.script_file.loc[i]
        #step 4.1: grabing the next row in script file, and getting a refenrence of the excel file
        self.before_buildings = self.bna[(self.bna['iteration']==i) & (self.bna['renewd']=='before')] #before buildings
        self.after_buildings = self.bna[(self.bna['iteration']==i) & (self.bna['renewd']=='after')] #after buildings
        self.before_buildings.reset_index(inplace=True)
        self.after_buildings.reset_index(inplace=True)
        #gather infromation on project
        self.bld_add_or_complex = self.next_row['bld_address']
        self.typeProject = self.next_row['TypeTitle']
        self.typeOperation = self.next_row['bld_operation']
        
        self.infoText.value = self.infoText.value + '\n Address or complex: ' + self.bld_add_or_complex
        self.infoText.value = self.infoText.value + '\n Type of project ' + self.typeProject

        #list of buildings
        self.list_of_bldgs = self.before_buildings.bldAdd.unique().tolist()
        self.list_of_bldgs_after = self.after_buildings.bldAdd.unique().tolist()
        self.invovlved_bldgs = self.list_of_bldgs + self.list_of_bldgs_after

    #helper function operation 12
    def operation_12(self):
        self.agent_i_merge = pd.merge(self.agent_i,self.after_buildings, how='left',left_on=['AgentBldAdd','AgentAppUnit'],right_on=['bldAdd','appUnits'])
        self.active_rows = self.agent_i.AgentBldAdd.isin(self.list_of_bldgs) #bofre Case 1-2 and Case 3
        self.active_rows_renters =  (self.active_rows & (self.agent_i['OwnerShip']==0)) #renters they all go!
        self.active_rows_owners =  (self.active_rows & (self.agent_i['OwnerShip']==1)) #owners go if their income is insufficent
        self.agent_i_merge.loc[self.active_rows_renters,'Agent_status']='leaving'

        self.agent_tax_ability = self.agent_i_merge[self.active_rows]['TaxAndMainTreshold']
        self.bld_expenses_price =  self.agent_i_merge[self.active_rows]['newMaintenace&Tax']
        self.agent_i_merge.loc[self.active_rows,'Can stay if own'] = (self.agent_tax_ability > self.bld_expenses_price)
        self.active_rows_owners_cannotStay =  (self.active_rows_owners & (self.agent_i_merge['Can stay if own']==False)) #both Owners who can't pay will leave
        self.agent_i_merge.loc[self.active_rows_owners_cannotStay,'Agent_status']='leaving'

        Current_residents_who_stay_rows = (self.active_rows & (self.agent_i_merge['Agent_status']=="staying"))
        crwsr = Current_residents_who_stay_rows #short writing
        self.staying_agents = self.agent_i_merge[crwsr][['AgentAppUnit','AgentBldAdd']]
        self.staying_agents['add_door'] = self.staying_agents['AgentBldAdd']+"_"+self.staying_agents['AgentAppUnit'].astype(str)
        #adding a building and door code

        self.after_buildings['add_door_2'] = self.after_buildings['bldAdd']+"_"+self.after_buildings['appUnits'].astype(str)
        self.avilable_units = ~self.after_buildings.add_door_2.isin(self.staying_agents['add_door']) #avilable units
        self.avilable_unitsin_bldg = self.after_buildings[self.avilable_units]
        self.avilable_unitsin_bldg.reset_index(inplace=True, drop=True)

    #helper function operation 3
    def operation_3(self):
        # 1. get only active owners
        # 2. reset their index
        # 3. merge with new buidling
        # 4. check ability to pay rent
        # 5. update their active living
        # 5. overwrite agent_i_file using the agentID (delete them and append them)
        self.agent_i_merge = self.agent_i.copy()
        self.active_rows = self.agent_i.AgentBldAdd.isin(self.list_of_bldgs) #choose tennats who live in these projects
        self.active_rows_renters =  (self.active_rows & (self.agent_i['OwnerShip']==0)) #renters they all go!
        self.active_rows_owners =  (self.active_rows & (self.agent_i['OwnerShip']==1)) #owners go if their income is insufficent
        self.agent_i_merge.loc[self.active_rows_renters,'Agent_status']='leaving' #mark renters as agents who will move out

        # 1. get only active owners - tenets who own their property and future will be determine on their income...
        
        self.activeOwnerAgents = self.agent_i_merge[self.active_rows_owners]
        
        # 2. reset their index
        self.activeOwnerAgents.reset_index(inplace=True) # so we can matched the new buildings to those agents
        self.activeOwnerAgents = self.activeOwnerAgents[['Age', 'AgeGroup', 'AgeGroupDesc', 'AgentAppUnit',
        'AgentBldAdd', 'AgentID', 'AgentIncome', 'AgentPurchaseThreshold',
        'AgentRentThreshold', 'AgentWealth', 'Agent_status', 'BuyTreshold',
        'IncomeDesc', 'IncomeNum', 'NativeDesc', 'Native_Group',
        'Native_Seniority', 'OwnerShip', 'OwnershipDesc', 'RentTreshold',
        'TaxAndMainTreshold']]
        # 3. merge with new buidling
        self.activeOwnerAgents_merge = pd.merge(self.activeOwnerAgents,self.after_buildings, how='left', left_index=True, right_index=True)
        # 4. check ability to pay rent
        self.agent_tax_ability = self.activeOwnerAgents_merge['TaxAndMainTreshold']
        self.bld_expenses_price =  self.activeOwnerAgents_merge['newMaintenace&Tax']
        self.activeOwnerAgents_merge['Can stay if own'] = (self.agent_tax_ability > self.bld_expenses_price)
        # 5. update their active living
        self.survived_agentsBool =  self.activeOwnerAgents_merge['Can stay if own']==True
        self.leavingAgentsBool =  self.activeOwnerAgents_merge['Can stay if own']==False
        self.activeOwnerAgents_merge.loc[self.leavingAgentsBool,['Agent_status']]='leaving'
        
        self.update_leave_agents_list = self.activeOwnerAgents_merge[self.leavingAgentsBool].AgentID.to_list()
        self.agent_i_merge.loc[self.agent_i_merge.AgentID.isin(self.update_leave_agents_list),['Agent_status']]='leaving' #update leaving agents
        
        self.survived_agents_update = self.activeOwnerAgents_merge[self.survived_agentsBool][['AgentID','AgentBldAdd','AgentAppUnit']]
        self.updated_bldg_slim =self.after_buildings[['bldAdd','appUnits']]
        # Change the address of the agents
        self.newAddress_for_agents = pd.merge(self.survived_agents_update,self.updated_bldg_slim, how='left', left_index=True, right_index=True)
        self.newAddress_for_agents = self.newAddress_for_agents[['AgentID','bldAdd','appUnits']]
        #update agents Pool
        self.change_agent_bool = self.agent_i_merge.AgentID.isin(self.newAddress_for_agents['AgentID'].tolist())
        self.agent_i_merge.loc[self.change_agent_bool,'AgentBldAdd'] = self.newAddress_for_agents.bldAdd.tolist()
        self.agent_i_merge.loc[self.change_agent_bool,'AgentAppUnit'] =self. newAddress_for_agents.appUnits.tolist()
        #select all the units left
        self.next_row1 = max(self.newAddress_for_agents.index)  + 1
        self.avilable_unitsin_bldg = self.after_buildings.iloc[self.next_row1:] #rows for constructing new agents
        self.avilable_unitsin_bldg.reset_index(inplace=True, drop=True)

    #hlper function post opoerstion for operation 12 and 3
    def operation_post_123(self,i):

        self.newAgents = self.generateAgensts(self.avilable_unitsin_bldg)
        self.agentsCol = self.newAgents.columns.tolist()
        #self.agentsCol.append('AgentID')
        #updating the agents file
        self.agent_i = self.agent_i_merge[self.agentsCol]
        self.agent_i = self.agent_i.append(self.newAgents)
        #self.agent_i['projectID_itr'] = self.next_row.FuturePlanID
        self.agent_i.reset_index(inplace=True)
        ## TO DO fix AgentID track the agent movement from old to new building or use UUID
        #self.agent_i['AgentID'] = self.agent_i.index #find a better way to track the Agents maybe use UUID or use a smarter way to track the movement of the agent!!!
        ## TO DO
        #self.list_of_bldgs
        self.agent_i.loc[self.agent_i.AgentBldAdd.isin(self.invovlved_bldgs),'projectID_itr'] = self.next_row.FuturePlanID
        self.agent_i['iteration'] = str(i)
        if (i==0):
            self.agents_all_iterations = self.agent_i
        else:
            self.agents_all_iterations = self.agents_all_iterations.append(self.agent_i)


    #Helper function sort of unpivot -- needs to be modified    
    def agent_mod_unpivot(self):
        agent_mod = self.agent_ref.copy()
        #Unpivot - This function needs to be converted to a real unpivot

        #Age
        agent_mod.loc[agent_mod['AgeGroupDesc']=='Young','Young']=True
        agent_mod.loc[agent_mod['AgeGroupDesc']=='Old','Old']=True

        #ownership
        agent_mod.loc[agent_mod['OwnershipDesc']=='Owner','Owner']=True
        agent_mod.loc[agent_mod['OwnershipDesc']=='Rent','Rent']=True


        #Income
        agent_mod.loc[agent_mod['IncomeDesc']=='Low Income','Low Income']=True
        agent_mod.loc[agent_mod['IncomeDesc']=='Medium Income','Medium Income']=True
        agent_mod.loc[agent_mod['IncomeDesc']=='High Income','High Income']=True
        return agent_mod
        

    #generate Agents
    def generateAgensts(self,thisDS):
        #this function recievs data from new building dataset and returns new renters or owners
        nUnits = len(thisDS['appUnits'])

        rand_income_rent = np.random.randint(0, high=5000, size=nUnits, dtype='l') #monthly income
        rand_inc_sr_rent =  pd.Series(rand_income_rent) #turning this into series

        rand_income_own = np.random.randint(3000, high=15000, size=nUnits, dtype='l') #monthly income
        rand_inc_sr_own =  pd.Series(rand_income_own) #into series
        
        rand_wealth = np.random.randint(0, high=5000000, size=nUnits, dtype='l') #wealth
        age = np.random.randint(25, high=110, size=nUnits, dtype='l') #wealth
        ownership = np.random.randint(0, high=2, size=nUnits, dtype='l') #0 rent 1 owns
        
        agent_new_ID = list(range(self.PopNum_forID,self.PopNum_forID+nUnits))
        self.PopNum_forID = self.PopNum_forID + nUnits # update the number for generating new agents next time
        ds = pd.DataFrame()
        
        ds['OwnerShip'] = pd.Series(ownership)
        ds['AgentAppUnit'] = thisDS['appUnits'] #what unit does the agent live in
        ds['AgentBldAdd'] = thisDS['bldAdd'] # in what bld address does the Agent live in

    
        ds['AgentWealth'] = pd.Series(rand_wealth)
        
        ds['AgentPurchaseThreshold'] = (ds['AgentWealth'] * 0.3).astype(int) # 30% of wealth, Agent can buy a house without Mortgage
        ds['Age'] = pd.Series(age)
        
        ds['AgeGroup'] = ds['Age'].apply(lambda x: 0 if x < 65 else 1)
        ds['Native_Seniority'] = 0
        ds['Native_Group'] = ds['Native_Seniority'].apply(lambda x: 0 if x < 10 else 1) # 0 Native, 1 NewComer
        
        # for renters take the rent price
        ds.loc[ds['OwnerShip']==0,'AgentIncome'] = (thisDS[ds['OwnerShip']==0]['rentPerMonth'])/0.3 + rand_inc_sr_rent[ds['OwnerShip']==0]
        ds.loc[ds['OwnerShip']==1,'AgentIncome'] = (thisDS[ds['OwnerShip']==1]['newMaintenace&Tax'])/0.3 + rand_inc_sr_own[ds['OwnerShip']==1]
        ds['AgentIncome'] = ds['AgentIncome'].astype(int)
        ds['AgentRentThreshold'] = (ds['AgentIncome'] * 0.3).astype(int) # 30% of income
        
        #Age Formating
        ds['AgeGroupDesc'] = ds['Age'].apply(lambda x: 'Young' if x < 65 else 'Old')
        #Native Formating
        ds['NativeDesc'] = ds['Native_Group'].apply(lambda x: 'Native' if x == 1 else 'New Comers')
        #Ownership Formating
        ds['OwnershipDesc'] = ds['OwnerShip'].apply(lambda x: 'Owner' if x == 1 else 'Rent')
        
        LowInc = int(self.rules['Income']['Low']['0'])
        MediumInc = int(self.rules['Income']['Medium']['1'])
        HighInc = int(self.rules['Income']['High']['2'])
        
        ds['IncomeNum'] = ds['AgentIncome'].apply(lambda x: "0" if x < LowInc else "1" if x < MediumInc else "2")
        ds['IncomeDesc'] = ds['AgentIncome'].apply(lambda x: 'Low Income' if x < LowInc else 'Medium Income' if x < MediumInc else "High Income")
        ds = self.updateAgentsThresholdData(ds,'new comers')
        ds['AgentID']=pd.Series(agent_new_ID)

        return ds
    
    #Helper function
    def updateAgentsThresholdData(self,ds,status):
        #This function recieves a Agent Dataset
        #The function returns the agents ability to live in a certain building as column data
        ds['TaxAndMainTreshold'] = ds['AgentIncome']*0.3
        ds['RentTreshold'] = ds['AgentIncome']*0.3
        ds['BuyTreshold'] = ds['AgentWealth']*0.3
        ds['Agent_status'] = status #staying, leaving,newComers buying always starts with staying
        return ds
    
    def saveAgentsExcel(self): 
        #simulation_folder
        simulation_path = self.sim_folder+self.simulation_name.value+"/"
        if not os.path.exists(simulation_path):
            os.mkdir(simulation_path)

        excel_file_name = 'agents_ssi.xlsx'
        excel_path = simulation_path+excel_file_name
        self.agents_all_iterations.to_excel(excel_path)

    #Convert From ESPG 2039 (Israel TM Grid) to ESPG 4326 (WGS 84)
    @staticmethod
    def Convert_2039_2_4326(feature):
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

