import pandas as pd
import numpy as np
#import geopandas as gpd
#from shapely.geometry import Point
#import folium
import json
#import os
import ipywidgets as widgets
#from datetime import datetime
#from datetime import date
from IPython.display import HTML, display

#Postgres
import psycopg2  # (if it is postgres/postgis)

class SSA:

    def __init__(self):
        pd.set_option("display.max_columns",100)
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
            value='agents_ssi.xlsx',
            description = 'Agent File'
            )
        
        #dt = datetime.now()
        #d1 = dt.strftime("%m%d_%H%M")
        sim_name="agents_cim_0331_1000"
        self.simulation_name = widgets.Text(
            value=sim_name,
            description='Simulation Name'
            )
    
        #This function Loads the master script files
    
    def load_files(self):
        self.sim_folder='simulationID/'+self.simulation_folder.value+'/'
        script_path = self.sim_folder+self.library["script_file"]
        #master script
        self.script_file = pd.read_excel(script_path)

        path_to_agents = self.sim_folder+ self.simulation_name.value + '/' + self.agents_name.value
        self.agent_ref = pd.read_excel(path_to_agents)
        
        self.agent_ref = self.agent_ref[['OwnerShip', 'AgentAppUnit', 'AgentBldAdd',
        'AgentWealth', 'AgentPurchaseThreshold', 'Age', 'AgeGroup',
       'Native_Seniority', 'Native_Group', 'AgentIncome', 'AgentRentThreshold',
       'AgeGroupDesc', 'NativeDesc', 'OwnershipDesc', 'IncomeNum',
       'IncomeDesc', 'TaxAndMainTreshold', 'RentTreshold', 'BuyTreshold',
       'Agent_status', 'AgentID', 'projectID_itr', 'iteration']]
       
        self.num_of_iterations = np.max(self.agent_ref.iteration.unique())
    
    def pivot_by_agents(self):
        noi = self.num_of_iterations
        self.agent_pivots =  self.agent_ref[self.agent_ref['iteration']==noi]
        self.agent_pivots
        self.agent_pivots['ones'] = 1
        self.agent_pivots.reset_index(inplace=True,drop=True)

        # pivot by Who is staying
        self.pivot_status = self.agent_pivots.pivot(index='AgentID',columns='Agent_status',values='ones')
        del self.pivot_status.index.name
        #self.agent_pivots[['laeving','new comers','staying']] = self.pivot_status
        self.agent_pivots = pd.merge(self.agent_pivots,self.pivot_status, how='left', left_index=True, right_index=True)
        
        
        self.agent_pivots = self.simplePivot(self.agent_pivots,'IncomeDesc') #pivot by Income
        self.agent_pivots = self.simplePivot(self.agent_pivots,'OwnershipDesc') #pivot by OwnershipDesc
        self.agent_pivots = self.simplePivot(self.agent_pivots,'NativeDesc') #pivot by NativeDesc
        self.agent_pivots = self.simplePivot(self.agent_pivots,'AgeGroupDesc') #pivot by AgeGroupDesc

    def simplePivot(self,ds, byCol):
        
        pivot_status = ds.pivot(index='AgentID',columns=byCol,values='ones')
        del pivot_status.index.name
        ds = pd.merge(ds,pivot_status, how='left', left_index=True, right_index=True)
        return ds
        