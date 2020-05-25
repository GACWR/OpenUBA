from pandas import DataFrame
from dataset import DatasetSession, CoreDataFrame, ES


class ESGeneric():
    def __init__(self, host: str, query: str):

        dataset_session: DatasetSession = DatasetSession("es")
        dataset_session.read_es_index(host, query)
        self.data: DataFrame = CoreDataFrame(dataset_session.es_dataset.dataframe)
