import os
# from google.colab import userdata

from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_huggingface import (
    HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
)
from langchain.schema import HumanMessage
from langchain_core.output_parsers import StrOutputParser
# from langchain_core.output_parsers
from langchain.chat_models import init_chat_model

#langgraph
from langgraph.graph.message import add_messages
from langgraph.graph import END,START, StateGraph

from typing import Annotated
from typing_extensions import TypedDict

from pydantic import BaseModel,Field
# from IPython.display import Image, display
import json
import pandas as pd
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool

from helper.data_center import load_db


class employee_state(TypedDict):
    query:str
    re_written_query:str
    sql_query:str
    context:str
    answer:str


#NODE 1

class RewriteOutput(BaseModel):
  response:str=Field(...,description='The rewritten query from the LLM')

query_rewrite="""<s>[INST] Rewrite the following user query to be short, simple, and clear. Preserve the original meaning.

Examples:

1. Original: how many days has the employee worked from the day he was hired.
   Rewritten: Number of days of the employee from today till the hired date.

2. Original: how many employees have joined the company in the year 2024, list them in descending order
   Rewritten: list all employees in descending order who joined in 2024

3. Original: list all the employees who is working in the company and has supervisor as Anand
   Rewritten: list all employees who have supervisor Anand

Now rewrite the following:

Original: {user_question}
Rewritten: [/INST]

return the output in this format
{{
  "re-written-query":"the re written query"
}}
"""



rewrite_user_query_prompt=PromptTemplate(template=query_rewrite)
llm = HuggingFaceEndpoint(
repo_id="meta-llama/Llama-3.2-3B-Instruct",
task="text-generation"
)
parser=StrOutputParser()
model = ChatHuggingFace(llm=llm)


def user_query_rewrite(state:employee_state):
    query_rewrite_response=(
    rewrite_user_query_prompt
    | model
    | parser
)
    response=query_rewrite_response.invoke(state['query'])
    return {
        're_written_query':response
    }



#NODE 2
##SQL statement LLM
class QueryOutput(BaseModel):
  query:str=Field(...,description='generated query')

SQL_llm = init_chat_model("mistral-large-latest", 
                          model_provider="mistralai",
                          max_tokens=5000)    

structure_output_llm=SQL_llm.with_structured_output(QueryOutput)   

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

def generate_sql_query(state:employee_state):
  db=load_db()
  chain=(
      query_prompt_template | structure_output_llm 
  )
  result=chain.invoke({
    "dialect":db.dialect,
    "table_info":db.table_info,
    "input":state['re_written_query']
})
  return{
      "sql_query":result
  }

#NODE 3
db=load_db()
def execute_the_query(state:employee_state):
  execute_query_tool = QuerySQLDatabaseTool(db=db) 
  response=execute_query_tool(state['sql_query'].query)
  return {
      "context":response
  }


#NODE 4
import ast
def clean_up_string(_cus):
    if not _cus or _cus.strip() == "":
        return ""
    try:
        # Safely evaluate the string to a Python object
        data = ast.literal_eval(_cus)

        # Check if it's a list with at least one tuple
        if isinstance(data, list) and len(data) > 0:
            _s=''
            for i in range(len(data)):
                _s+=f'{i+1} '+' '.join([str(item) for item in data[i]])+'\n'
            return _s
        else:
            return str(_cus)
    except Exception as ex:
        # In case it's not a valid Python literal
        return ex

def answer_from_context(state:employee_state):
  cleaned_context=clean_up_string(state['context'])
  prompt='''
  <s>[INST] Use the following context to answer the user's question. If the answer is not in the context, respond with "I don't know."

Context:
{context}

Question:
{question}

Answer: [/INST]
  '''
  context_prompt=PromptTemplate(
      template=prompt,
      input_variables=['context','question']
  )

  chain=(
      context_prompt
      | model
      | parser
  )
  result=chain.invoke({
      "context":state['context'],
      "question":state['query']
  })
  state['answer']=result
  return state
  

def build_graph():
    graph_builder=StateGraph(employee_state)

    graph_builder.add_node('rewrite_query',user_query_rewrite)
    graph_builder.add_node('get_SQL_statements',generate_sql_query)
    graph_builder.add_node('execute_sql_query',execute_the_query)
    graph_builder.add_node('answer_from_context',answer_from_context)

    graph_builder.add_edge(START,'rewrite_query')
    graph_builder.add_edge('rewrite_query','get_SQL_statements')
    graph_builder.add_edge('get_SQL_statements','execute_sql_query')
    graph_builder.add_edge('execute_sql_query','answer_from_context')
    graph_builder.add_edge('answer_from_context',END)
    return graph_builder.compile()
    