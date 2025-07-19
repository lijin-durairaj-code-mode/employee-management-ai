from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_huggingface import (
    HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
)
from langchain.schema import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.output_parsers import StructuredOutputParser, ResponseSchema

#langgraph
from langgraph.graph.message import add_messages
from langgraph.graph import END,START, StateGraph
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

#common
from typing import Annotated, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel,Field
import pandas as pd
from logger.log import logger
# from logger import logger

#custom
from utils.data_center import load_db
from prompts_template.templates import (
    system_message, query_rewrite, context_prompt, rewrite_3_prompt)
from prompts_template.prompting_class import(
    QueryOutput,QueryInput,RewriteOutput,RewriteQueryOutputFormat
)
from models.waila_employee_state import employee_state
from dotenv import load_dotenv

load_dotenv()    
logger=logger()
db=load_db()

#NODE -1 
# re-writting user query
rewrite_user_query_prompt=PromptTemplate(template=query_rewrite)
llm = HuggingFaceEndpoint(
repo_id="meta-llama/Llama-3.2-3B-Instruct",
task="text-generation"
)

model = ChatHuggingFace(llm=llm)

def user_query_rewrite(state:employee_state):
    logger.log_info('NODE - 1')
    logger.log_info('user_query_rewrite')
    state['times_of_user_response']=0
    parser=StrOutputParser()
    try:
        query_rewrite_response=(
        rewrite_user_query_prompt
        | model
        | parser
    )
        response=query_rewrite_response.invoke({
            'user_question':state['query']
            })
        
        return {
            're_written_query':response
        }
    except Exception as ex:
        return ex


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
  logger.log_info('NODE - 2')
  logger.log_info('generate_sql_query')
  db=load_db()
  chain=(
      query_prompt_template | structure_output_llm 
    
  )
  try:
    result=chain.invoke({
    "dialect":db.dialect,
    "table_info":db.table_info,
    "input":state['re_written_query']
    })
    logger.log_info(f'generated SQL query {result}')  
    state['times_of_user_response']=state.get('times_of_user_response',0)+1
    state["sql_query"]=result
    return state
  except Exception as ex:
      logger.log_info(ex)
      return "rewrite_query"
 


#NODE 3
# executing the generated SQL statement

def execute_the_query(state:employee_state):
  logger.log_info('NODE - 3')
  logger.log_info('execute_the_query')
  execute_query_tool = QuerySQLDatabaseTool(db=db) 
  response=execute_query_tool(state['sql_query'].query)
  
  return {
      "context":response
  }

#NODE 4
# getting the context and the question to answer from the LLM
import ast
def clean_up_string(_cus):
    logger.log_info('clean_up_string')
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
    logger.log_info('NODE - 4')
    logger.log_info('answer_from_context')
    state['context']= clean_up_string(state.get('context',''))
    parser=StrOutputParser()

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
    

def conditional_direct(state:employee_state)->Literal['create_options_query','answer_from_context']:
    logger.log_info('conditional_direct')
    logger.log_info(state)
    if state.get('context','') =='' and state.get('times_of_user_response',0)<=1:
        logger.log_info('inside create options query')        
        return "create_options_query"
    else:
        logger.log_info('inside answer from context')
        return "answer_from_context"
    

#NODE 5
# radio button options
schema = [
    ResponseSchema(
        name='answer',
        description='List of 3 re-written queries that are short and easy to understand.'
    )
]
parser = StructuredOutputParser.from_response_schemas(schema)
format_instructions = parser.get_format_instructions()

radio_button_options_prompt=PromptTemplate(
    template=rewrite_3_prompt,
     input_variables=['input_question'],
    partial_variables={"format_instructions": format_instructions}
)

def create_options_query(state:employee_state):
    logger.log_info('NODE - 5')
    logger.log_info('create_options_query')
    llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.2-3B-Instruct",
    task="text-generation"
    )
    model = ChatHuggingFace(llm=llm)
    chain=(
    radio_button_options_prompt
    | model
    | parser
)
    response=chain.invoke({
    "input_question":state['query']
})
    state['options_query_arr']=response
    return state


#NODE 6
#human in loop
def human_in_loop(state:employee_state):    
    logger.log_info('human_in_loop')
    value=interrupt('enter a generated new question')
    logger.log_info('interrupt executed')
    logger.log_info(value)
    state['re_written_query']=value
    return state


def build_graph():
    checkpointer=MemorySaver()
    graph_builder=StateGraph(employee_state)

    #adding nodes
    graph_builder.add_node('rewrite_query',user_query_rewrite) 
    graph_builder.add_node('generate_sql_query',generate_sql_query) 
    graph_builder.add_node('execute_the_query',execute_the_query)
    graph_builder.add_node('answer_from_context',answer_from_context)
    graph_builder.add_node('create_options_query',create_options_query) 
    graph_builder.add_node('human_in_loop',human_in_loop) 

    #adding edges
    graph_builder.add_edge(START,'rewrite_query')  
    graph_builder.add_edge('rewrite_query','generate_sql_query')    
    graph_builder.add_edge('generate_sql_query','execute_the_query')

    graph_builder.add_conditional_edges("execute_the_query",conditional_direct)

    graph_builder.add_edge('answer_from_context',END)
    graph_builder.add_edge('create_options_query','human_in_loop')
    graph_builder.add_edge('human_in_loop','generate_sql_query')

    graph=graph_builder.compile(checkpointer=checkpointer)
    return graph


# graph=build_graph()

# graph.get_graph().draw_mermaid_png()

    