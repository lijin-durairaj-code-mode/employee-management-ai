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

#common methods
from dotenv import load_dotenv
from datetime import datetime
import ast

#custom methods
from prompts.templates import query_prompt_template,answer_prompt
from helper.data_center import load_db
from helper.prompting_template import QueryOutput,QueryInput

#fatsapi
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware


app=FastAPI()
app.add_middleware(SessionMiddleware,secret_key='some_secret_key')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],             # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],               # e.g., ["GET", "POST"]
    allow_headers=["*"],               # e.g., ["Authorization"]
)

load_dotenv()
db=load_db()

def clean_up_string(s):
    if not s or s.strip() == "":
        return ""
    try:
        # Safely evaluate the string to a Python object
        data = ast.literal_eval(s)

        # Check if it's a list with at least one tuple
        if isinstance(data, list) and len(data) > 0:
            _s=''
            for i in range(len(data)):
                _s+=' '.join([str(item) for item in data[i]])
            return _s
        else:
            return str(data)
    except Exception:
        # In case it's not a valid Python literal
        return s

def intial_load():
    parser=StrOutputParser()

    llm = init_chat_model("mistral-large-latest", 
                          model_provider="mistralai",
                          max_tokens=5000)    

    structure_output_llm=llm.with_structured_output(QueryOutput)   

    execute_query_tool = QuerySQLDatabaseTool(db=db)  

    chain=(
        RunnableMap(
            {
                'question':lambda x:x['input'],
                'context':(query_prompt_template | structure_output_llm 
                           | RunnableLambda(lambda x:x.query) | execute_query_tool 
                           | RunnableLambda(clean_up_string)
                           )
            }
        )        
        | answer_prompt
        | llm
        | parser
    )
    return chain

@app.get('/', response_class=HTMLResponse)
def welcome(request:Request):
  request.session.clear()


@app.post('/question')
async def fetch_employee_details(request:Request,question:QueryInput):
  
  session =request.session  

  if "page_load" not in request.session:
     session['page_load']="first load"
     
  if session['page_load'] =="first load": 
    session['page_load']="second load"  
    chain=intial_load()
    app.state.chain = chain
    response=chain.invoke({
     "dialect": db.dialect,
    "table_info": db.table_info,
    "input": question.query,
})
    
    return response
  else:
    chain = getattr(app.state, "chain", None)
    if not chain:
        return JSONResponse(status_code=500, content={"error": "Chain not initialized"})
    response=chain.invoke({
     "dialect": db.dialect,
    "top_k": 10,
    "table_info": db.table_info,
    "input": question.query,
})
    
    return response


  