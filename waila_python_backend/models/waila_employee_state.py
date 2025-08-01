
from typing import Annotated
from typing_extensions import TypedDict

#--------------------##----------------------##-----------------------##--------------


class employee_state(TypedDict):
    query:str
    re_written_query:str
    sql_query:str
    context:str
    answer:str
    options_query_arr:str
    times_of_user_response:int
    