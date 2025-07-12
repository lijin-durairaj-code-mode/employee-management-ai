#langchain
from langchain_huggingface import (
    HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import (
    RunnableLambda, RunnablePassthrough, RunnableMap
)
from langchain_core.prompts import (
    PromptTemplate,ChatPromptTemplate,MessagesPlaceholder
)
from langchain.output_parsers import (
    StructuredOutputParser, ResponseSchema
)
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

#langgraphs
from langgraph.graph import END,START, StateGraph

#common imports
from dotenv import load_dotenv
from datetime import datetime
import ast

#custom methods imports
from prompts_template.templates import query_prompt_template,answer_prompt
from utils.data_center import load_db
from prompts_template.prompting_class import QueryOutput, QueryInput
from prompts_template.user_query_rewrite_prompt import  query_rewrite
from models.waila_employee_state import employee_state
from waila_python_backend.utils.common import build_graph



#fatsapi
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
#----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####----#####




@asynccontextmanager
async def intial_load(app:FastAPI):   
    app.state.graph=build_graph()
    yield


app=FastAPI(lifespan=intial_load)

app.add_middleware(SessionMiddleware,secret_key='some_secret_key')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],               # e.g., ["GET", "POST"]
    allow_headers=["*"],               # e.g., ["Authorization"]
)



@app.get('/', response_class=HTMLResponse)
def welcome(request:Request):
    return '<h1>hello</h1>'
  
@app.post('/question')
async def fetch_employee_details(request:Request,question:QueryInput):
    graph = request.app.state.graph
    result=graph.invoke({
         'query':question
    })    
    
    return result


  