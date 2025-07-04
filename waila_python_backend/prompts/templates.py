from langchain_core.prompts import (
    PromptTemplate,ChatPromptTemplate,MessagesPlaceholder
)

from langchain_core.prompts.string import (
    
    StringPromptTemplate, 
)

system_message = """
Given an input question, create a syntactically correct {dialect} query to
run to help find the answer. Unless the user specifies in his question a
specific number of examples they wish to obtain. You can order the results by a relevant column to
return the most interesting examples in the database.

Schema:
Table: employeelist
Columns:
- emailId: Email of the Employee
- name: Name of the Employee
- employeeId: Employee Id of the Employee
- country: Country of the Employee
- Designation: Designation of the Employee
- LastPromotionDate: Last promotion date of the Employee
- JobTitle: Job title of the employee
- HiredDate: Hired date of the employee
- EmergencyContactName: Emergency contact Name of the Employee
- EmergencyContactNumber: Emergency contact number of the Employee
- RegionalSupervisor: Regional Supervisor of the Employee
- OfficeSupervisor: Office Supervisor of the office where Employee is working

Never query for all the columns from a specific table, only ask for a the
few relevant columns given the question.

Only run Select statement, Never run Update / Delete query

Pay attention to use only the column names that you can see in the schema
description. Be careful to not query for columns that do not exist. Also,
pay attention to which column is in which table.

Only use the following tables:
{table_info}
"""

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", "Question: {input}")],
    input_variables=["dialect","table_info","input"]
    
)

answer_prompt=PromptTemplate(
    template='''
   You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
   If you don't know the answer, just say that you don't know and ask the User to try with some different question.
    Question: who is henry shah
    Context: Henry Shah 0987
    Answer: Henry Shah is an employee with the id 0987

    Question: how many employees are there from uganda
    Context: 33
    Answer: There are in total of 33 employees from uganda


    Question: {question} 
    Context: {context} 
    Answer:
    ''',
    input_variables=['question','context']
)