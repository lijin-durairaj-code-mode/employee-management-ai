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

from utils.data_center import load_db
from prompts_template.templates import system_message, query_rewrite, context_prompt
from prompts_template.prompting_class import QueryOutput,QueryInput,RewriteOutput
from models.waila_employee_state import employee_state
from dotenv import load_dotenv

load_dotenv()    

#NODE #re-writting the user query

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
##generating SQL statement LLM

# SQL_llm = init_chat_model("mistral-large-latest", model_provider="mistralai")  
SQL_llm = init_chat_model("llama3-8b-8192", model_provider="groq")

# llm = HuggingFaceEndpoint(
# repo_id="mistralai/Mistral-Large-Instruct-2411",
# task="text-generation"
# )
# SQL_llm = ChatHuggingFace(llm=llm)

structure_output_llm=SQL_llm.with_structured_output(QueryOutput)   

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
# executing the generated SQL statement
db=load_db()
def execute_the_query(state:employee_state):
  execute_query_tool = QuerySQLDatabaseTool(db=db) 
  response=execute_query_tool(state['sql_query'].query)
  _r=clean_up_string(response)
  return {
      "context":response
  }


#NODE 4
# getting the context and the question to answer from the LLM
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
                _s+=' '.join([str(item) for item in data[i]])
            return _s
        else:
            return str(_cus)
    except Exception as ex:
        # In case it's not a valid Python literal
        return ex

def answer_from_context(state:employee_state):
  state['context']= clean_up_string(state['context'])
 
  _context_prompt=PromptTemplate(
      template=context_prompt,
      input_variables=['context','question']
  )

  chain=(
      _context_prompt
      | model
      | parser
  )
  result= chain.invoke({
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
    # graph_builder.add_edge('get_SQL_statements',END)
    graph_builder.add_edge('get_SQL_statements','execute_sql_query')
    graph_builder.add_edge('execute_sql_query','answer_from_context')
    graph_builder.add_edge('answer_from_context',END)
    return graph_builder.compile()
    