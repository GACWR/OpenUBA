from pandas import DataFrame
from dataset import DatasetSession, CoreDataFrame

class LocalPandasCSV():
    def __init__(self,
                 file_path: str,
                 sep: str,
                 header: int,
                 error_bad_lines: bool,
                 warn_bad_lines: bool):

        dataset_session: DatasetSession = DatasetSession("disk")

        dataset_session.read_csv("../test_datasets/toy_1", "proxy", "disk", sep)

        self.data: DataFrame = CoreDataFrame(dataset_session.dataset.dataframe)
