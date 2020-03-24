import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
import json
import os
import ipywidgets as widgets


class DC:

    def __init__(self):
        #reference dictionary file
        #----------------------Loading Library and rule files
        path_1 = 'library_march_24.json'
        with open(path_1) as json_file:
            self.library = json.load(json_file)
        print_library = json.dumps(self.library, indent=2)

        #rules dictionary file file
        path_2 = 'rules.json'
        with open(path_2) as json_file:
            self.rules = json.load(json_file)
        print_rules = json.dumps(self.rules, indent=2)
        #print('-----Rules File-------')
        #print(print_rules)
        #print('-----Rules Library-------')
        #print(print_library)

        ##-------------setup widgets-----------------------
        self.cim_name = widgets.Text(
            value='cim_0324_0620',
            description='Simulation Name:',
            )

    def setup_cim_path_and_load_scripts(self):
        ## Setup cimulation Path and loading essential scripts
        #Cimulation path
        self.cim_path = self.library['cim_folder']
        self.script_file = self.library['script_file']
        self.cim_specific_path = self.cim_path+self.cim_name.value + '/'
        self.script_path = self.cim_specific_path+self.script_file

        #Future script path
        self.future_file = self.library['future_script']
        self.future_path = self.cim_specific_path+self.future_file

        print(self.future_path)

        print(self.script_path)

        self.script = pd.read_excel(self.script_path)
        self.script_ft =  pd.read_excel(self.future_path)

    def initiating_agents(self):
        self.Agents = pd.DataFrame()
        #Agents Widget
        self.agents_name = widgets.Text(
            value='agents.xlsx',
            description='Agents File Name:',
            )
        max_line = self.script.index[-1] + 1
        #description Widget
        self.i_slider = widgets.IntSlider(
            min=0,
            max =max_line,
            description = 'Iteration'
        )
    
    def iterate(self):

        i = self.i_slider.value
        print('Iteration '+ str(i))
        currentBldg = self.script.loc[i]
        agents_path =self.cim_specific_path+self.agents_name.value

        if (currentBldg.bld_operation < 3):
            current_bldg_ds = pd.DataFrame() #current Building Dataset
            Future_bldg_ds = pd.DataFrame()  #future Building Dataset
            subAgents_ds = pd.DataFrame()    #subAgents Dataset
            # Need to create one list with all the buildings! think about Case 3
            
            #original building
            cb = self.iterate_case_12_original_building(currentBldg)
            #Future building or construction
            self.fb = self.iterate_case_12_future_building(currentBldg)
            #Update Agents
            self.iterate_case_12_generateAgents(currentBldg,cb)

        else:
            print('oh oh operation 3!')
            #operation 3 means that it's a Polygon not a single building
            [self.before_dem,self.after_dem] = self.iterate_case_3(currentBldg)

            bldg_path = self.library['bldg_path']
            self.after_dem.reset_index(inplace=True)
            last_line1 = len(self.before_dem.index)
            last_line2 = len(self.after_dem.index)
            agents_path =self.cim_specific_path+self.agents_name.value

            self.iterate_case_3_current_building(last_line1,currentBldg,bldg_path,agents_path)
            self.iterate_case_3_future_building(last_line2,currentBldg,bldg_path)

        self.agents_format(agents_path) #format nicely the agents excel file

    def run_iterations(self):
        for i in range(0,self.script.index[-1]):
            self.i_slider.value = i
            self.iterate()

    def iterate_case_12_original_building(self,currentBldg):
        #helper function 
        #original building
        cb = self.def_currentBld_op12_ds(currentBldg)
        bldg_path = self.library['bldg_path']
        sp_bldg_before_path = self.cim_specific_path + bldg_path + currentBldg.ExcelBefore
        cb.to_excel(sp_bldg_before_path) #Need to append in Long List
        return cb
    
    def iterate_case_12_future_building(self,currentBldg):
        #helper function 
        #Future building
        futureBldg = self.script_ft[self.script_ft['bld_address']==currentBldg['bld_address']]
        fb = self.def_futureBld_op12_ds(futureBldg,currentBldg)
        bldg_path = self.library['bldg_path']
        sp_bldg_after_path = self.cim_specific_path + bldg_path + currentBldg.ExcelChange
        fb.to_excel(sp_bldg_after_path)
        return fb
    
    def iterate_case_12_generateAgents(self,currentBldg,cb):
        rent_percent = currentBldg['originalRentPercent']
        ng = self.generateAgensts(cb,rent_percent)
        self.Agents = self.Agents.append(ng)
        self.Agents.reset_index(inplace=True)
        self.Agents['AgentID'] = self.Agents.index
        self.Agents = self.Agents[['AgentAppUnit', 'AgentBldAdd', 'AgentIncome', 'AgentWealth','AgentPurchaseThreshold', 'AgentRentThreshold', 'Age',
            'OwnerShip', 'AgeGroup', 'Native_Seniority', 'Native_Group', 'AgentID']]
        agents_path =self.cim_specific_path+self.agents_name.value
        self.Agents.to_excel(agents_path)



    def iterate_case_3(self,currentBldg):
        get_complex_xlsx = currentBldg.ExcelPolygon
        bldg_path = self.library['bldg_path']
        sp_bldg_folder_path = self.cim_specific_path + bldg_path
        bldg_path_xlsx= sp_bldg_folder_path+get_complex_xlsx
        print(bldg_path_xlsx)
        inside_script = pd.read_excel(bldg_path_xlsx)
        before_dem = inside_script[inside_script.status=='destroyed']
        after_dem = inside_script[inside_script.status=='New Building']
        return [before_dem,after_dem]

    def def_currentBld_op12_ds(self, this_line):
        ds = pd.DataFrame()
        
        nUnits = this_line.OriginalUnits
        unitNumber = [k for k in range(nUnits)]
        
        ds['appUnits'] = unitNumber
        ds['AppSize'] = this_line.OriginalHouseSize
        ds['bldAdd']  = this_line['bld_address']
        ds['sellPerMeter'] = this_line.purchase_p
        ds['rentPerMeter'] = this_line.rent_price
        
        ds['ArnonaTarif'] = float(self.rules['ArnonaTax'])
        ds['ArnonaTax'] = ds['ArnonaTarif'] * ds['AppSize']
        
        ds['sellPrice'] = ds['AppSize'] * ds['sellPerMeter']
        ds['rentPerMonth'] = ds['AppSize'] * ds['rentPerMeter'] + this_line.Maintenace +  ds['ArnonaTax']
        ds['maintenace&Tax'] = this_line.Maintenace + ds['ArnonaTax']
        
        
        if (this_line.bld_operation == 1):
            ds['status'] = 'Old Building'
        else:
            ds['status'] = 'Demolished'
        return ds
    
    def def_futureBld_op12_ds(self, this_line,currentBldg):
        ds = pd.DataFrame()
        nUnits = int(this_line.TotalUnits)
        unitNewNumber = [k for k in range(nUnits)]
        ds['appUnits'] = unitNewNumber
        indx = this_line.index[0]
        ds['bldAdd'] = this_line.loc[indx]['bld_address']
        ds['AppSize'] = float(this_line.AvrgTotaalArea)
        ds['sellPerMeter'] = float(round(this_line.purchase_p * ( 1 + this_line.priceIncrease ),1))
        ds['rentPerMeter'] = float(round(this_line.rent_price * ( 1 + this_line.rentIncrease ),1))
        
        ds['ArnonaTarif'] = float(self.rules['ArnonaTax'])
        ds['ArnonaTax'] = round(ds['ArnonaTarif'] * ds['AppSize'],1)
        
        ds['sellPrice'] = round(ds['AppSize'] * ds['sellPerMeter'],1)
        ds['rentPerMonth'] = round(ds['AppSize'] * ds['rentPerMeter'] + float(this_line.newMaintenace) + ds['ArnonaTax'],1)
        
        ds['newMaintenace&Tax'] = ds['ArnonaTax']  + float(this_line.newMaintenace)
        #ds['newMaintenace&Tax'] = ds['ArnonaTax'] 
        if (currentBldg.bld_operation ==1 ):
            ds['status'] = 'Tama 38_1'
        else:
            ds['status'] = 'Tama 38_2'
        return ds

    def iterate_case_3_current_building(self,last_line1,currentBldg,bldg_path,agents_path):
        for j in range(0,last_line1):
            if (j==0):
                current_bldg_ds = pd.DataFrame()
                subAgents_ds = pd.DataFrame()
            print(j)
            before_line = self.before_dem.loc[j]
            current_bldg_ds = current_bldg_ds.append(self.def_currentBld_op3_ds(before_line))
            if (j==last_line1-1):
                print('last line!')
                bldg_path_before_xlsx =self.cim_specific_path + bldg_path + currentBldg.ExcelBefore
                current_bldg_ds.reset_index(inplace=True)
                current_bldg_ds.to_excel(bldg_path_before_xlsx)
                subAgents_ds = self.generateAgensts(current_bldg_ds)

                self.Agents = self.Agents.append(subAgents_ds)
                self.Agents.reset_index(inplace=True)
                self.Agents['AgentID'] = self.Agents.index
                self.Agents = self.Agents[['AgentAppUnit', 'AgentBldAdd', 'AgentIncome', 'AgentWealth','AgentPurchaseThreshold', 'AgentRentThreshold', 'Age',
                    'OwnerShip', 'AgeGroup', 'Native_Seniority', 'Native_Group', 'AgentID']]
                self.Agents.to_excel(agents_path) # No Need to save every Iteration.


    def iterate_case_3_future_building(self,last_line2,currentBldg,bldg_path):
        for j in range(0,last_line2):
            Future_bldg_ds = pd.DataFrame()
            after_line = self.after_dem.loc[j]
            Future_bldg_ds = Future_bldg_ds.append(self.def_FutureBld_op3_ds(after_line))
            if (j==last_line2-1):
                bldg_path_after_xlsx = self.cim_specific_path + bldg_path + currentBldg.ExcelChange
                Future_bldg_ds.reset_index(inplace=True)
                Future_bldg_ds.to_excel(bldg_path_after_xlsx)

    def def_currentBld_op3_ds(self,before_line):
        ds = pd.DataFrame()
        nUnits = before_line.OriginalUnits
        unitNumber = [k for k in range(nUnits)]
        
        ds['appUnits'] = unitNumber
        ds['bldAdd'] = before_line.bld_address
        ds['AppSize'] = before_line.OriginalHouseSize
        ds['sellPerMeter'] = before_line.purchase_p
        ds['rentPerMeter'] = before_line.rent_price

        ds['ArnonaTarif'] = float(self.rules['ArnonaTax'])
        ds['ArnonaTax'] = ds['ArnonaTarif'] * ds['AppSize']
        
        ds['sellPrice'] = ds['AppSize'] * ds['sellPerMeter']
        ds['rentPerMonth'] = ds['AppSize'] * ds['rentPerMeter'] + before_line.Maintenace +  ds['ArnonaTax']
        ds['maintenace&Tax'] = before_line.Maintenace +  ds['ArnonaTax']
        ds['status'] = 'Demolished'
        return ds


    def def_FutureBld_op3_ds(self,after_line):
        ds = pd.DataFrame()
        nUnits = int(after_line.TotalUnits)
        unitNewNumber = [k for k in range(nUnits)]
        ds['appUnits'] = unitNewNumber
        ds['bldAdd'] = after_line.bld_address
        ds['AppSize'] = after_line.AvrgTotaalArea
        ds['sellPerMeter'] = after_line.purchase_p * ( 1 + after_line.priceIncrease )
        ds['rentPerMeter'] = after_line.rent_price * ( 1 + after_line.rentIncrease )

        
        ds['ArnonaTarif'] = float(self.rules['ArnonaTax'])
        ds['ArnonaTax'] = ds['ArnonaTarif'] * ds['AppSize']
        
        ds['sellPrice'] = ds['AppSize'] * ds['sellPerMeter']
        ds['rentPerMonth'] = ds['AppSize'] * ds['rentPerMeter'] + after_line.newMaintenace + ds['ArnonaTax'] 
        
        ds['newMaintenace&Tax'] = after_line.newMaintenace + ds['ArnonaTax'] 
        ds['status'] = 'New Building'
        return ds
            

    def generateAgensts(self, thisDS, per = 0.5):
        nUnits = len(thisDS['appUnits'])
        #unitNumber = [k for k in range(nUnits)]
        
        rand_income_rent = np.random.randint(0, high=5000, size=nUnits, dtype='l') #monthly income
        rand_inc_sr_rent =  pd.Series(rand_income_rent)

        rand_income_own = np.random.randint(3000, high=15000, size=nUnits, dtype='l') #monthly income
        rand_inc_sr_own =  pd.Series(rand_income_own)
        
        rand_wealth = np.random.randint(0, high=5000000, size=nUnits, dtype='l') #wealth
        age = np.random.randint(25, high=110, size=nUnits, dtype='l') #wealth
        
        #ownership!
        P=[per,1-per]
        ownership = np.random.choice(2,size = nUnits,p=P)
        #ownership = np.random.randint(0, high=2, size=nUnits, dtype='l') #0 rent 1 owns
        
        ds = pd.DataFrame()
        
        ds['OwnerShip'] = pd.Series(ownership)
        ds['AgentAppUnit'] = thisDS['appUnits'] #what unit does the agent live in
        ds['AgentBldAdd'] = thisDS['bldAdd'] # in what bld address does the Agent live in
    
        ds['AgentWealth'] = pd.Series(rand_wealth)
        
        ds['AgentPurchaseThreshold'] = ds['AgentWealth'] * 0.3 # 30% of wealth, Agent can buy a house without Mortgage
        ds['Age'] = pd.Series(age)
        
        ds['AgeGroup'] = ds['Age'].apply(lambda x: 0 if x < 65 else 1)
        ds['Native_Seniority'] = ds['Age'].apply(DC.getRandomSeniority)
        ds['Native_Group'] = ds['Native_Seniority'].apply(lambda x: 0 if x < 10 else 1) # 0 Native, 1 NewComer
        
        # for renters take the rent price
        ds.loc[ds['OwnerShip']==0,'AgentIncome'] = (thisDS[ds['OwnerShip']==0]['rentPerMonth'])/0.3 + rand_inc_sr_rent[ds['OwnerShip']==0]
        ds.loc[ds['OwnerShip']==1,'AgentIncome'] = (thisDS[ds['OwnerShip']==1]['maintenace&Tax'])/0.3 + rand_inc_sr_own[ds['OwnerShip']==1]
        ds['AgentRentThreshold'] = ds['AgentIncome'] * 0.3 # 30% of income
        return ds

    def agents_format(self,agents_path):
        self.Agents['AgentIncome'] = self.Agents['AgentIncome'].astype(int)
        #Age Formating
        self.Agents['AgeGroupDesc'] = self.Agents['Age'].apply(lambda x: 'Young' if x < 65 else 'Old')
        #Native Formating
        self.Agents['NativeDesc'] = self.Agents['Native_Group'].apply(lambda x: 'Native' if x == 1 else 'New Comers')
        #Ownership Formating
        self.Agents['OwnershipDesc'] = self.Agents['OwnerShip'].apply(lambda x: 'Owner' if x == 1 else 'Rent')
        LowInc = int(self.rules['Income']['Low']['0'])
        MediumInc = int(self.rules['Income']['Medium']['1'])
        HighInc = int(self.rules['Income']['High']['2'])
        self.Agents['IncomeNum'] = self.Agents['AgentIncome'].apply(lambda x: "0" if x < LowInc else "1" if x < MediumInc else "2")
        self.Agents['IncomeDesc'] = self.Agents['AgentIncome'].apply(lambda x: 'Low Income' if x < LowInc else 'Medium Income' if x < MediumInc else "High Income")
        self.Agents.to_excel(agents_path)

    @staticmethod
    def getRandomSeniority(age):
        max_seniority = 50
        min_seniority = 10
        if age > 50:
            max_seniority = 50
            min_seniority = 10
        else:
            max_seniority = age
            min_seniority = 10
        return np.random.randint(min_seniority, high=max_seniority, size=1, dtype='l')[0]
    