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
        #print_library = json.dumps(self.library, indent=2)

        #rules dictionary file file
        path_2 = 'rules.json'
        with open(path_2) as json_file:
            self.rules = json.load(json_file)
        #print_rules = json.dumps(self.rules, indent=2)
        #print('-----Rules File-------')
        #print(print_rules)
        #print('-----Rules Library-------')
        #print(print_library)

        ##-------------setup widgets-----------------------
        self.cim_name = widgets.Text(
            value='cim_0325_0640',
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

        #Future Polygon Script Path

        self.future_pol_file = self.library['future_polygons_script']
        self.future_pol_path = self.cim_specific_path+self.future_pol_file


        self.script = pd.read_excel(self.script_path)
        self.script_ft =  pd.read_excel(self.future_path)
        self.script_ft_pol = pd.read_excel(self.future_pol_path)

        #Before and After File
        self.bldg_path = self.library['bldg_path']
        self.before_n_after_xlsx = self.cim_specific_path + self.bldg_path + 'before_n_after.xlsx'

    def initiating_agents(self):
        self.Agents = pd.DataFrame()
        self.before_bldgs = pd.DataFrame() # place Holder for old buildings
        self.after_bldgs = pd.DataFrame() # place holder for after buildings
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
        # this function operates one iteration
        # it determines the case
            #create a list of current units
            #create a list of future untis
            # generates agents according to the percent of renters
            #append all those list

        i = self.i_slider.value
        print('Iteration '+ str(i))
        currentBldg = self.script.loc[i]
        self.agents_path =self.cim_specific_path+self.agents_name.value
        #all_bldgs = pd.DataFrame() # Place Holder for all buidlings

        if (currentBldg.bld_operation < 3):
            # Need to create one list with all the buildings! think about Case 3
            #original building
            self.cb = self.def_currentBld_op12_ds(currentBldg) #prepare a list of original units
            self.before_bldgs = self.before_bldgs.append(self.cb) #append the list to the grand list
            #Future building or construction
            self.fb = self.iterate_case_12_future_building(currentBldg) #prepare a list of future units
            self.after_bldgs = self.after_bldgs.append(self.fb) #append the list to the grand list
            #Update Agents
            rent_percent = float(currentBldg['originalRentPercent'])
            subAgents_ds = self.generateAgensts(self.cb,rent_percent)
            self.Agents = self.Agents.append(subAgents_ds)
        else:
            print('oh oh operation 3!')
            #operation 3 means that it's a Polygon not a single building
            [self.before_dem,self.after_dem] = self.iterate_case_3(currentBldg) #grab a list of building in project before and after demolishen

            #grab the number of rows for poejct before and after demolishen
            last_line1 = len(self.before_dem.index) 
            last_line2 = len(self.after_dem.index)

            self.current_bldg_ds = self.iterate_case_3_current_building(last_line1,currentBldg) #prepare list of units
            self.before_bldgs = self.before_bldgs.append(self.current_bldg_ds) # append list of units
            subAgents_ds = self.generateAgensts(self.current_bldg_ds) # generate agents
            self.Agents = self.Agents.append(subAgents_ds)           # append agents

            self.future_bldg_ds = self.iterate_case_3_future_building(last_line2,currentBldg) #prepare units of future units
            self.after_bldgs = self.after_bldgs.append(self.future_bldg_ds) #append them
    
    #run all iterations
    def run_iterations(self):
        for i in range(0,self.script.index[-1]+1):
            self.i_slider.value = i
            self.iterate()
        self.agents_format() #format nicely the agents excel file
        self.before_n_after = self.before_bldgs.append(self.after_bldgs)
        self.before_n_after.to_excel(self.before_n_after_xlsx)


    #extract list of buildings fromTama 38 projects   
    def iterate_case_12_future_building(self,currentBldg):
        #helper function 
        #Future building
        futureBldg = self.script_ft[self.script_ft['bld_address']==currentBldg['bld_address']]
        fb = self.def_futureBld_op12_ds(futureBldg,currentBldg)
        return fb

    #extract list of buildings before and after demolishen
    def iterate_case_3(self,currentBldg):
        inside_script = self.script_ft_pol[self.script_ft_pol['FuturePlanID']==currentBldg.FuturePlanID]
        before_dem = inside_script[inside_script.status=='destroyed']
        before_dem.reset_index(inplace=True)
        after_dem = inside_script[inside_script.status=='New Building']
        after_dem.reset_index(inplace=True)
        return [before_dem,after_dem]

    #generate dataset for existing building units
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
        ds['renewd'] ='before'
        ds['PlanID'] = this_line.FuturePlanID
        ds['iteration'] = this_line['index']

        return ds

    #generate dataset for future building units   
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
        ds['renewd'] ='after'
        ds['PlanID'] = currentBldg.FuturePlanID
        ds['iteration'] = currentBldg['index']
        return ds
    
    #iterate for every building in current complex buildings
    def iterate_case_3_current_building(self,last_line1,currentBldg):
        current_bldg_ds = pd.DataFrame()
        subAgents_ds = pd.DataFrame()
        for j in range(0,last_line1):
            print(j)
            before_line = self.before_dem.loc[j]
            current_bldg_ds = current_bldg_ds.append(self.def_currentBld_op3_ds(before_line,currentBldg))
        return(current_bldg_ds)

    #iterate for every building in the new taba project
    def iterate_case_3_future_building(self,last_line2,currentBldg):
        for j in range(0,last_line2):
            Future_bldg_ds = pd.DataFrame()
            after_line = self.after_dem.loc[j]
            Future_bldg_ds = Future_bldg_ds.append(self.def_FutureBld_op3_ds(after_line,currentBldg))

        return Future_bldg_ds

    #Generate units in housing projects that are fate is to be demolished
    def def_currentBld_op3_ds(self,before_line,cb):
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
        ds['renewd'] ='before'
        ds['PlanID'] = cb.FuturePlanID
        ds['iteration'] = cb['index']
        return ds

    #Generate new units in the new Taba Projects
    def def_FutureBld_op3_ds(self,after_line,cb):
        ds = pd.DataFrame()
        nUnits = int(after_line.TotalUnits)
        unitNewNumber = [k for k in range(nUnits)]
        ds['appUnits'] = unitNewNumber
        ds['bldAdd'] = after_line.bld_address +'n'
        ds['AppSize'] = after_line.AvrgTotaalArea
        ds['sellPerMeter'] = after_line.purchase_p * ( 1 + after_line.priceIncrease )
        ds['rentPerMeter'] = after_line.rent_price * ( 1 + after_line.rentIncrease )

        
        ds['ArnonaTarif'] = float(self.rules['ArnonaTax'])
        ds['ArnonaTax'] = ds['ArnonaTarif'] * ds['AppSize']
        
        ds['sellPrice'] = ds['AppSize'] * ds['sellPerMeter']
        ds['rentPerMonth'] = ds['AppSize'] * ds['rentPerMeter'] + after_line.newMaintenace + ds['ArnonaTax'] 
        
        ds['newMaintenace&Tax'] = after_line.newMaintenace + ds['ArnonaTax'] 
        ds['status'] = 'New Building'
        ds['renewd'] ='after'
        ds['PlanID'] = cb.FuturePlanID
        ds['iteration'] = cb['index']
        return ds
   
    #Based on the percentage of renters and the current listing of units, generate new agents           
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
        ds['AgentAppUnit'] = thisDS['appUnits'].to_list() #what unit does the agent live in
        ds['AgentBldAdd'] = thisDS['bldAdd'].to_list() # in what bld address does the Agent live in
    
        ds['AgentWealth'] = pd.Series(rand_wealth)
        
        ds['AgentPurchaseThreshold'] = ds['AgentWealth'] * 0.3 # 30% of wealth, Agent can buy a house without Mortgage
        ds['Age'] = pd.Series(age)
        
        ds['AgeGroup'] = ds['Age'].apply(lambda x: 0 if x < 65 else 1)
        ds['Native_Seniority'] = ds['Age'].apply(DC.getRandomSeniority)
        ds['Native_Group'] = ds['Native_Seniority'].apply(lambda x: 0 if x < 10 else 1) # 0 Native, 1 NewComer
        
        # for renters take the rent price
        thisDS.reset_index(inplace=True)
        ds.loc[ds['OwnerShip']==0,'AgentIncome'] = ((thisDS[ds['OwnerShip']==0]['rentPerMonth'])/0.3 + rand_inc_sr_rent[ds['OwnerShip']==0]).to_list()
        ds.loc[ds['OwnerShip']==1,'AgentIncome'] = ((thisDS[ds['OwnerShip']==1]['maintenace&Tax'])/0.3 + rand_inc_sr_own[ds['OwnerShip']==1]).to_list()
        ds['AgentRentThreshold'] = (ds['AgentIncome'] * 0.3).to_list() # 30% of income
        return ds

    #Format The agents so the excel sheet will look better
    def agents_format(self):
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
        #self.Agents.drop(columns='level_0',inplace=True)
        self.Agents.reset_index(drop=True,inplace=True)
        self.Agents['AgentID'] = self.Agents.index
        self.Agents.to_excel(self.agents_path)

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
    