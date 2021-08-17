from typing import Optional

from citrine.resources.dataset import Dataset, DatasetCollection
from citrine.resources.file_link import FileCollection
from tests.utils.fakes.fake_file_collection import FakeFileCollection


class FakeDataset(Dataset):

    def __init__(self):
        pass

    @property
    def files(self) -> FileCollection:
        return FakeFileCollection()


class FakeDatasetCollection(DatasetCollection):

    def __init__(self, project_id, session):
        DatasetCollection.__init__(self, project_id=project_id, session=session)
        self.datasets = []

    def register(self, model: Dataset) -> Dataset:
        self.datasets.append(model)
        return model

    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return self.datasets
        else:
            return self.datasets[(page - 1)*per_page:page*per_page]