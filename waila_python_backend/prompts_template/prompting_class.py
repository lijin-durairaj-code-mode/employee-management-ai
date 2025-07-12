from pydantic import BaseModel,Field

class QueryOutput(BaseModel):
  query:str=Field(...,description='generated query')


class QueryInput(BaseModel):
  query:str=Field(...,description='query for genarting response from LLM')

class RewriteOutput(BaseModel):
  response:str=Field(...,description='The rewritten query from the LLM')
  
class RewriteQueryOutputFormat(BaseModel):
  query:list=Field(...,description='The re-written user query')