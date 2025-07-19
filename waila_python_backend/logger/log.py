import logging

class logger:

    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.log=logging.getLogger(__name__)

    def log_info(self,method):
        print(f'--method name: {method}')
    
    def log_error(self,error):
        self.log.error(error)