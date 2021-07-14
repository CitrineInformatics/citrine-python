from uuid import uuid4, UUID
from typing import Iterator, Union, Optional
import pytest

from gemd.entity.link_by_uid import LinkByUID

from citrine.informatics.data_sources import DataSource
from citrine.resources.design_execution import DesignExecution, DesignExecutionCollection
from citrine.resources.design_space import DesignSpace, DesignSpaceCollection
from citrine.resources.design_workflow import DesignWorkflow, DesignWorkflowCollection
from citrine.resources.gemtables import GemTable, GemTableCollection
from citrine.resources.material_run import MaterialRun
from citrine.resources.predictor import Predictor, GraphPredictor, PredictorCollection
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflow
from citrine.resources.predictor_evaluation_workflow import PredictorEvaluationWorkflowCollection
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecution
from citrine.resources.predictor_evaluation_execution import PredictorEvaluationExecutionCollection
from citrine.resources.project import Project
from citrine.resources.table_config import TableConfig, TableConfigCollection, TableBuildAlgorithm
from citrine._rest.collection import Collection

from citrine.builders.auto_configure import AutoConfigureWorkflow


@pytest.fixture()
def fake_project():
    """Fake project that returns auto-configured assets."""

    # Collections
    class FakeCollection(Collection):
        def __init__(self):
            pass

        def build(self):
            pass

        def delete(self, uid):
            pass

        def register(self, asset):
            asset.uid = uuid4()
            return asset

    class FakeTableConfigCollection(TableConfigCollection, FakeCollection):
        def __init__(self):
            pass

        def default_for_material(self, **kwargs):
            return FakeTableConfig()

    class FakeGemTableCollection(GemTableCollection, FakeCollection):
        def __init__(self):
            pass

        def build_from_config(self, *args, **kwargs) -> GemTable:
            table = FakeGemTable()
            table.version = 1
            return table

    class FakePredictorCollection(PredictorCollection, FakeCollection):
        def __init__(self):
            pass

        def auto_configure(self, **kwargs) -> Predictor:
            predictor = FakePredictor()
            return predictor

    class FakePredictorEvaluationWorkflowCollection(PredictorEvaluationWorkflowCollection, FakeCollection):
        def __init__(self):
            pass

        def create_default(self, **kwargs) -> PredictorEvaluationWorkflow:
            return FakePredictorEvaluationWorkflow()

    class FakePredictorEvaluationExecutionCollection(PredictorEvaluationExecutionCollection, FakeCollection):
        def __init__(self):
            pass

        def trigger(self, *args):
            return FakePredictorEvaluationExecution()

    class FakeDesignSpaceCollection(DesignSpaceCollection, FakeCollection):
        def __init__(self):
            pass

        def create_default(self, *kwargs) -> DesignSpace:
            return FakeDesignSpace()

    class FakeDesignWorkflowCollection(DesignWorkflowCollection, FakeCollection):
        def __init__(self):
            pass

    class FakeDesignExecutionCollection(DesignExecutionCollection, FakeCollection):
        def __init__(self):
            pass

        def trigger(self, *args):
            return FakeDesignExecution()

    # Resources
    class FakeTableConfig(TableConfig):
        def __init__(self):
            pass

    class FakeGemTable(GemTable):
        def __init__(self):
            pass

    class FakePredictor(Predictor):
        def __init__(self):
            pass

    class FakePredictorEvaluationWorkflow(PredictorEvaluationWorkflow):
        def __init__(self):
            pass

        def executions(self) -> PredictorEvaluationExecutionCollection:
            return FakePredictorEvaluationExecutionCollection()

    class FakePredictorEvaluationExecution(PredictorEvaluationExecution):
        def __init__(self):
            pass

    class FakeDesignSpace(DesignSpace):
        def __init__(self):
            pass

    class FakeDesignWorkflow(DesignWorkflow):
        def __init__(self):
            pass

        def design_executions(self) -> DesignExecutionCollection:
            return FakeDesignExecutionCollection()

    class FakeDesignExecution(DesignExecution):
        def __init__(self):
            pass

    class FakeProject(Project):
        def __init__(self):
            pass

        @property
        def table_configs(self) -> TableConfigCollection:
            return FakeTableConfigCollection()

        @property
        def tables(self) -> GemTableCollection:
            return FakeGemTableCollection()

        @property
        def predictors(self) -> PredictorCollection:
            return FakePredictorCollection()

        @property
        def predictor_evaluation_workflows(self) -> PredictorEvaluationWorkflowCollection:
            return FakePredictorEvaluationWorkflowCollection()

        @property
        def predictor_evaluation_executions(self) -> PredictorEvaluationExecutionCollection:
            return FakePredictorEvaluationExecutionCollection()

        @property
        def design_spaces(self) -> DesignSpaceCollection:
            return FakeDesignSpaceCollection()

        @property
        def design_workflows(self) -> DesignWorkflowCollection:
            return FakeDesignWorkflowCollection()

    return FakeProject()


@pytest.fixture()
def fake_config(fake_project: Project):
    return AutoConfigureWorkflow(project=fake_project, name='Fake v1')


def test_auto_configure_raises(fake_config: AutoConfigureWorkflow, fake_project: Project):
    """Ensure it throws if passed incorrect arguments."""
    mr = MaterialRun(name='Sample Material')
    table = fake_project.tables.build_from_config()
    fake_predictor = fake_project.predictors.auto_configure()

    # Bad mode
    with pytest.raises(TypeError):
        fake_config.from_material(
            material=mr,
            mode='BAD MODE CHOICE'
        )

    # Bad mode
    with pytest.raises(TypeError):
        fake_config.from_table(
            table=table,
            mode='BAD MODE CHOICE'
        )

    # Predictor not registered
    with pytest.raises(ValueError):
        fake_config.from_predictor(
            predictor=fake_predictor
        )
