from typing import Optional
from uuid import uuid4

from citrine.exceptions import NotFound
from citrine.resources.project import Project, ProjectCollection
from tests.utils.fakes import FakeDatasetCollection
from tests.utils.fakes import FakeDesignSpaceCollection, FakeDesignWorkflowCollection
from tests.utils.fakes import FakeGemTableCollection, FakeTableConfigCollection
from tests.utils.fakes import FakePredictorCollection, FakePredictorEvaluationWorkflowCollection
from tests.utils.fakes import FakePredictorEvaluationExecutionCollection
from tests.utils.fakes import FakeDescriptorMethods
from tests.utils.session import FakeSession


class FakeProjectCollection(ProjectCollection):

    def __init__(self, search_implemented: bool = True):
        ProjectCollection.__init__(self, session=FakeSession)
        self.projects = []
        self.search_implemented = search_implemented

    def register(self, name: str, description: Optional[str] = None) -> Project:
        project = FakeProject(name=name)
        self.projects.append(project)
        return project

    def list(self, page: Optional[int] = None, per_page: int = 100):
        if page is None:
            return self.projects
        else:
            return self.projects[(page - 1)*per_page:page*per_page]

    def search(self, search_params: Optional[dict] = None, per_page: int = 100):
        if not self.search_implemented:
            raise NotFound("search")

        ans = self.projects
        if search_params.get("name"):
            method = search_params["name"]["search_method"]
            value = search_params["name"]["value"]
            if method == "EXACT":
                ans = [x for x in ans if x.name == value]
            elif method == "SUBSTRING":
                ans = [x for x in ans if value in x.name]
        if search_params.get("description"):
            method = search_params["description"]["search_method"]
            value = search_params["description"]["value"]
            if method == "EXACT":
                ans = [x for x in ans if x.description == value]
            elif method == "SUBSTRING":
                ans = [x for x in ans if value in x.description]

        return ans

    def delete(self, uuid):
        raise NotImplementedError


class FakeProject(Project):

    def __init__(self, name="foo", description="bar", num_properties=3, session=FakeSession()):
        super().__init__(name=name, description=description, session=session)
        self.uid = uuid4()
        self._design_spaces = FakeDesignSpaceCollection(self.uid, self.session)
        self._design_workflows = FakeDesignWorkflowCollection(self.uid, self.session)
        self._descriptor_methods = FakeDescriptorMethods(num_properties)
        self._datasets = FakeDatasetCollection(self.uid, self.session)
        self._predictors = FakePredictorCollection(self.uid, self.session)
        self._pees = FakePredictorEvaluationExecutionCollection(self.uid, self.session)
        self._pews = FakePredictorEvaluationWorkflowCollection(self.uid, self.session)
        self._tables = FakeGemTableCollection(self.uid, self.session)
        self._table_configs = FakeTableConfigCollection(self.uid, self.session)

    @property
    def datasets(self) -> FakeDatasetCollection:
        return self._datasets

    @property
    def design_spaces(self) -> FakeDesignSpaceCollection:
        return self._design_spaces

    @property
    def design_workflows(self) -> FakeDesignWorkflowCollection:
        return self._design_workflows

    @property
    def descriptors(self) -> FakeDescriptorMethods:
        return self._descriptor_methods

    @property
    def predictors(self) -> FakePredictorCollection:
        return self._predictors

    @property
    def predictor_evaluation_executions(self) -> FakePredictorEvaluationExecutionCollection:
        return self._pees

    @property
    def predictor_evaluation_workflows(self) -> FakePredictorEvaluationWorkflowCollection:
        return self._pews

    @property
    def tables(self) -> FakeGemTableCollection:
        return self._tables

    @property
    def table_configs(self) -> FakeTableConfigCollection:
        return self._table_configs

