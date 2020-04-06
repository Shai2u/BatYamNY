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

    def pivot_stay_leave_project(self):
        agent_1 = self.agent_ref.copy()
        agent_1['ones']=1
        agent_1['index_id']=agent_1.index
        agent_1.set_index("index_id")

        #s_ownership = agent_1.pivot(index='index_id', columns='OwnershipDesc',values='ones') #1
        s_status = agent_1.pivot(index='index_id', columns='Agent_status',values='ones') #2
        #s_income = agent_1.pivot(index='index_id', columns='IncomeDesc',values='ones') #3
        #s_native = agent_1.pivot(index='index_id', columns='NativeDesc',values='ones') #4
        #s_age_group = agent_1.pivot(index='index_id', columns='AgeGroupDesc',values='ones') #5
        s_iteration = agent_1['iteration'] #6
        s_project = agent_1['projectID_itr'] #7

        filter_by_project = s_project.notnull() # grab only the rows where we had a project
        proejct_values = s_project[filter_by_project].unique()
        stays_leaves_project = s_status[filter_by_project].join([s_iteration[filter_by_project]])
        stays_leaves_project_gb = stays_leaves_project.groupby('iteration')
        stays_leaves_sum = stays_leaves_project_gb.sum()
        stays_leaves_sum['Total staying'] = stays_leaves_sum['new comers']+stays_leaves_sum['staying']
        stays_leaves_sum['totalPop'] = stays_leaves_sum['Total staying'] + stays_leaves_sum['laeving']
        stays_leaves_sum['leaving Percent'] = stays_leaves_sum['laeving']/stays_leaves_sum['totalPop'] #new comers
        stays_leaves_sum['new comers Percent'] = stays_leaves_sum['new comers']/stays_leaves_sum['totalPop'] #new comers
        stays_leaves_sum['staying Percent'] = stays_leaves_sum['staying']/stays_leaves_sum['totalPop'] #staying
        stays_leaves_sum['project_id']= proejct_values

        self.stays_leaves_sum = stays_leaves_sum
    
    def pivot_staying_agents_project(self):
        agent_1 = self.agent_ref.copy()
        agent_1['ones']=1
        agent_1['index_id']=agent_1.index
        agent_1.set_index("index_id")

        s_project = agent_1['projectID_itr'] #7
        filter_by_project = s_project.notnull()
        
        s_n_nc = agent_1['Agent_status']!='laeving' # filter by staying and new comers only

    
        s_ownership = agent_1[s_n_nc].pivot(index='index_id', columns='OwnershipDesc',values='ones') #1
        s_ownership = s_ownership[filter_by_project]

        s_status = agent_1.pivot(index='index_id', columns='Agent_status',values='ones') #2
        s_status = s_status[filter_by_project]
        
        s_income = agent_1[s_n_nc].pivot(index='index_id', columns='IncomeDesc',values='ones') #3
        s_income = s_income[filter_by_project]

        s_native = agent_1[s_n_nc].pivot(index='index_id', columns='NativeDesc',values='ones') #4
        s_native = s_native[filter_by_project]

        s_age_group = agent_1[s_n_nc].pivot(index='index_id', columns='AgeGroupDesc',values='ones') #5
        s_age_group = s_age_group[filter_by_project]

        s_iteration = agent_1['iteration'] #6
        s_iteration = s_iteration[filter_by_project]


        # By Project
        proejct_values = s_project[filter_by_project].unique()
        stays_leaves_project = s_status.join([s_ownership,s_income,s_native,s_age_group,s_iteration])
        stays_leaves_project_gb = stays_leaves_project.groupby('iteration')
        stays_leaves_sum = stays_leaves_project_gb.sum()
        stays_leaves_sum['Total staying'] = stays_leaves_sum['new comers']+stays_leaves_sum['staying']
        stays_leaves_sum['totalPop'] = stays_leaves_sum['Total staying'] + stays_leaves_sum['laeving']

        stays_leaves_sum['Leaving Percent'] = stays_leaves_sum['laeving']/stays_leaves_sum['totalPop']
        stays_leaves_sum['Staying Percent'] = stays_leaves_sum['staying']/stays_leaves_sum['totalPop']
        stays_leaves_sum['New Comer Percent'] = stays_leaves_sum['new comers']/stays_leaves_sum['totalPop']

        stays_leaves_sum['Owner Percet'] = stays_leaves_sum['Owner']/stays_leaves_sum['Total staying']       
        stays_leaves_sum['Rent Percet'] = stays_leaves_sum['Rent']/stays_leaves_sum['Total staying']       

        stays_leaves_sum['High Income Percet'] = stays_leaves_sum['High Income']/stays_leaves_sum['Total staying']
        stays_leaves_sum['Medium Income'] = stays_leaves_sum['Medium Income']/stays_leaves_sum['Total staying']            
        stays_leaves_sum['Low IncomeRent Percet'] = stays_leaves_sum['Low Income']/stays_leaves_sum['Total staying']


        stays_leaves_sum['Native Percet'] = stays_leaves_sum['Native']/stays_leaves_sum['Total staying']       
        stays_leaves_sum['New Comers Percet'] = stays_leaves_sum['New Comers']/stays_leaves_sum['Total staying']

        stays_leaves_sum['Old Percet'] = stays_leaves_sum['Old']/stays_leaves_sum['Total staying']       
        stays_leaves_sum['Young Percet'] = stays_leaves_sum['Young']/stays_leaves_sum['Total staying']   

        stays_leaves_sum['project_id']= proejct_values
        self.stays_leaves_sum = stays_leaves_sum
    
    def pivot_accumulation(self):
        agent_1 = self.agent_ref.copy()
        agent_1['ones']=1
        agent_1['index_id']=agent_1.index
        agent_1.set_index("index_id")

        s_ownership = agent_1.pivot(index='index_id', columns='OwnershipDesc',values='ones') #1
        s_status = agent_1.pivot(index='index_id', columns='Agent_status',values='ones') #2
        s_income = agent_1.pivot(index='index_id', columns='IncomeDesc',values='ones') #3
        s_native = agent_1.pivot(index='index_id', columns='NativeDesc',values='ones') #4
        s_age_group = agent_1.pivot(index='index_id', columns='AgeGroupDesc',values='ones') #5
        s_iteration = agent_1['iteration'] #6
        s_project = agent_1['projectID_itr'] #7

        proejct_values = s_project[s_project.notnull()].unique()

        accumulation = s_status.join(s_iteration)
        accumulation_gb = accumulation.groupby('iteration')
        accumulation_sum = accumulation_gb.sum()
        accumulation_sum['Total staying'] = accumulation_sum['new comers']+accumulation_sum['staying']
        accumulation_sum['project_id']= proejct_values

        agent_data = s_ownership.join([s_status,s_income,s_native,s_age_group,s_iteration,s_project])

        agent_data_2 = agent_data #No Filter
        agent_data_1 = agent_data[agent_data['laeving']!=1]
        ad_leaving = agent_data[agent_data['laeving']==1]
        
        agent_data_gb = agent_data_1.groupby('iteration')
        agent_data_sum = agent_data_gb.sum()
        agent_data_sum['Total Staying'] = agent_data_sum['Old'] + agent_data_sum['Young']
        ad_leaving_gb = ad_leaving.groupby('iteration')
        ad_leaving_sum = ad_leaving_gb.sum()

        ad_percent = agent_data_sum.copy()
        ad_percent['Leaving'] = ad_leaving_sum['laeving']
        ad_percent['Owner Percent'] = ad_percent['Owner']/ad_percent['Total Staying'] #Owners
        ad_percent['Rent Percent'] = ad_percent['Rent']/ad_percent['Total Staying'] #Owners
        ad_percent['new comers Percent'] = ad_percent['new comers']/ad_percent['Total Staying'] #new comers
        ad_percent['staying Percent'] = ad_percent['staying']/ad_percent['Total Staying'] #staying
        ad_percent['High Income Percent'] = ad_percent['High Income']/ad_percent['Total Staying'] #High Income
        ad_percent['Medium Income Percnet'] = ad_percent['Medium Income']/ad_percent['Total Staying'] #Medium Income
        ad_percent['Low Income Percent'] = ad_percent['Low Income']/ad_percent['Total Staying'] #Low Income
        ad_percent['Native Percnet'] = ad_percent['Native']/ad_percent['Total Staying'] #Native
        ad_percent['New Comers Percent'] = ad_percent['New Comers']/ad_percent['Total Staying'] #New Comers
        ad_percent['Old Percent'] = ad_percent['Old']/ad_percent['Total Staying'] #Old
        ad_percent['Young Percent'] = ad_percent['Young']/ad_percent['Total Staying'] #Young

        self.accumulated_agents_stat = ad_percent

        agent_data_gb2 = agent_data_2.groupby('iteration')
        agent_data_sum2 = agent_data_gb2.sum()
        agent_data_sum2['Total Staying'] = agent_data_sum2['new comers'] + agent_data_sum2['staying']

        ad_percent2 = agent_data_sum2.copy()
        ad_percent2['new comers Percent'] = ad_percent2['new comers']/ad_percent2['Total Staying'] #new comers
        ad_percent2['staying Percent'] = ad_percent2['staying']/ad_percent2['Total Staying'] #staying

        self.staying_leaving = ad_percent2[['laeving','new comers','staying','Total Staying','new comers Percent','staying Percent']]


