import sqlite3
import pandas as pd
from langchain_community.utilities import SQLDatabase


def load_db():    
    data=load_excel()
    conn = sqlite3.connect('my_database.db')
    data.to_sql('employeelist', conn, if_exists='replace', index=False)
    db = SQLDatabase.from_uri("sqlite:///my_database.db")
    return db

def load_excel():
    _data=pd.read_csv('./assests/employee-list.csv')
    employee_name=_data['name'].str.strip().str.split(r'\s+',expand=True).rename(columns={0:'employee_firstname',1:'employee_lastname'})
    regional_supervisor_name=_data['RegionalSupervisor'].str.strip().str.split(r'\s+',expand=True).rename(columns={0:'regional_supervisor_firstname',1:'regional_supervisor_lastname'})
    office_supervisor_name=_data['OfficeSupervisor'].str.strip().str.split(r'\s+',expand=True).rename(columns={0:'office_supervisor_firstname',1:'office_supervisor_lastname'})
    
    _data=_data.assign(**employee_name,**regional_supervisor_name,**office_supervisor_name).drop(
    ['name','RegionalSupervisor','OfficeSupervisor'],axis=1
    ).assign(
        name=lambda x:x.employee_firstname+' '+x.employee_lastname,
    regional_supervisor_name=lambda x:x.regional_supervisor_firstname+' '+x.regional_supervisor_lastname,
        office_supervisor_name=lambda x:x.office_supervisor_firstname+' '+x.office_supervisor_lastname
    ).drop(
        ['regional_supervisor_firstname','regional_supervisor_lastname','office_supervisor_firstname','office_supervisor_lastname','employee_firstname','employee_lastname'],axis=1
    ).assign(
        HiredDate=pd.to_datetime(_data['HiredDate'], format='%d-%m-%Y').dt.strftime('%Y-%m-%d')
    )
    return _data