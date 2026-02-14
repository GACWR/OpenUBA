'''
Copyright 2019-Present The OpenUBA Platform Authors
spark data loader for models
'''

from pandas import DataFrame
from core.dataset import CoreDataFrame
from core.integrations.spark import SparkConnector

class SparkDataLoader:
    '''
    data loader for spark tables
    loads data from spark into pandas dataframe for model processing
    '''
    
    def __init__(self, table_name: str, master_url: str = None):
        self.table_name = table_name
        self.connector = SparkConnector(master_url=master_url)
        self._data = None
    
    def get_data(self) -> DataFrame:
        '''
        get data from spark table as pandas dataframe
        '''
        if self._data is None:
            self.connector.connect()
            spark_df = self.connector.spark.table(self.table_name)
            # convert to pandas (for small to medium datasets)
            # for large datasets, models should process in spark directly
            self._data = spark_df.toPandas()
        return CoreDataFrame(self._data)
    
    @property
    def data(self) -> DataFrame:
        '''
        property accessor for data
        '''
        return self.get_data()


class SparkGeneric:
    '''
    generic spark data loader (alias for SparkDataLoader)
    provides compatibility with basic_model
    '''
    
    def __init__(self, table_name: str, master_url: str = None):
        self.loader = SparkDataLoader(table_name=table_name, master_url=master_url)
        self._data = None
    
    @property
    def data(self) -> DataFrame:
        '''
        property accessor for data
        '''
        if self._data is None:
            self._data = self.loader.get_data()
        return self._data

