from pydantic import BaseModel,Field

class QueryOutput(BaseModel):
  query:str=Field(...,description='generated query')


class QueryInput(BaseModel):
  query:str=Field(...,description='query for genarting response from LLM')