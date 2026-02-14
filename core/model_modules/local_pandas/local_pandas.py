from pandas import DataFrame
from core.dataset import DatasetSession, CoreDataFrame

class LocalPandasCSV():
    def __init__(self,
                 file_path: str,
                 file: str,
                 sep: str,
                 header: int,
                 error_bad_lines: bool,
                 warn_bad_lines: bool):

        dataset_session: DatasetSession = DatasetSession("disk")

        file_location: str = ''.join([file_path, file])

        # extract dataset name and file type from file path
        # file_path should be like "../test_datasets/toy_1" or "/path/to/dataset"
        # file should be like "proxy/bluecoat.log" or just "file.csv"
        dataset_name = file_path.split("/")[-1] if "/" in file_path else file_path
        file_type = file.split("/")[0] if "/" in file else "data"
        
        dataset_session.read_csv(file_path, file_type, "disk", sep)

        #assign data
        self.data: DataFrame = CoreDataFrame(dataset_session.csv_dataset.dataframe)

class LocalPandasParquet():
    def __init__(self,
                 file_path: str,
                 sep: str,
                 header: int,
                 error_bad_lines: bool,
                 warn_bad_lines: bool):

        #
        dataset_session: DatasetSession = DatasetSession("disk")

        dataset_session.read_parquet("../test_datasets/toy_1", "proxy", "disk", sep)

        #assign data
        self.data: DataFrame = CoreDataFrame(dataset_session.parquet_dataset.dataframe)
