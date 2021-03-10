
from typing import Iterator
from uuid import UUID

from citrine.resources.dataset import Dataset
from citrine.resources.data_concepts import DataConcepts
from citrine.resources.delete import DELETE_SERVICE_MAX
from citrine.resources.property_template import PropertyTemplateCollection, PropertyTemplate
from citrine.resources.condition_template import ConditionTemplateCollection, ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplateCollection, ParameterTemplate
from citrine.resources.process_template import ProcessTemplateCollection, ProcessTemplate
from citrine.resources.material_template import MaterialTemplateCollection, MaterialTemplate
from citrine.resources.measurement_template import MeasurementTemplateCollection, MeasurementTemplate
from citrine.resources.process_run import ProcessRunCollection, ProcessRun
from citrine.resources.material_run import MaterialRunCollection, MaterialRun
from citrine.resources.measurement_run import MeasurementRunCollection, MeasurementRun
from citrine.resources.ingredient_run import IngredientRunCollection, IngredientRun
from citrine.resources.process_spec import ProcessSpecCollection, ProcessSpec
from citrine.resources.material_spec import MaterialSpecCollection, MaterialSpec
from citrine.resources.measurement_spec import MeasurementSpecCollection, MeasurementSpec
from citrine.resources.ingredient_spec import IngredientSpecCollection, IngredientSpec
from citrine.seeding.dataset_deletes import wipe_dataset
from tests.utils.session import FakeSession

from gemd.demo.cake import make_cake, make_cake_templates, make_cake_spec, make_cake_templates
from gemd.util import flatten

import math
import pytest


@pytest.fixture
def fake_dataset():
    """Fake dataset that serves GEMD objects via collections' list_all methods."""

    cake_spec = make_cake_spec()
    cake_tmpls = make_cake_templates()
    gemds = [DataConcepts.build(gemd) for i in range(8) for gemd in flatten(make_cake(tmpl=cake_tmpls, cake_spec=cake_spec), "dummy")]


    class FakePropertyTemplateCollection(PropertyTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[PropertyTemplate]:
            return iter([x for x in gemds if isinstance(x, PropertyTemplate)])

    class FakeConditionTemplateCollection(ConditionTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ConditionTemplate]:
            return iter([x for x in gemds if isinstance(x, ConditionTemplate)])

    class FakeParameterTemplateCollection(ParameterTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ParameterTemplate]:
            return iter([x for x in gemds if isinstance(x, ParameterTemplate)])

    class FakeProcessTemplateCollection(ProcessTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ProcessTemplate]:
            return iter([x for x in gemds if isinstance(x, ProcessTemplate)])

    class FakeMaterialTemplateCollection(MaterialTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MaterialTemplate]:
            return iter([x for x in gemds if isinstance(x, MaterialTemplate)])

    class FakeMeasurementTemplateCollection(MeasurementTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MeasurementTemplate]:
            return iter([x for x in gemds if isinstance(x, MeasurementTemplate)])

    class FakeProcessRunCollection(ProcessRunCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ProcessRun]:
            return iter([x for x in gemds if isinstance(x, ProcessRun)])

    class FakeMaterialRunCollection(MaterialRunCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MaterialRun]:
            return iter([x for x in gemds if isinstance(x, MaterialRun)])

    class FakeMeasurementRunCollection(MeasurementRunCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MeasurementRun]:
            return iter([x for x in gemds if isinstance(x, MeasurementRun)])

    class FakeIngredientRunCollection(IngredientRunCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[IngredientRun]:
            return iter([x for x in gemds if isinstance(x, IngredientRun)])

    class FakeProcessSpecCollection(ProcessSpecCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ProcessSpec]:
            return iter([x for x in gemds if isinstance(x, ProcessSpec)])

    class FakeMaterialSpecCollection(MaterialSpecCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MaterialSpec]:
            return iter([x for x in gemds if isinstance(x, MaterialSpec)])

    class FakeMeasurementSpecCollection(MeasurementSpecCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[MeasurementSpec]:
            return iter([x for x in gemds if isinstance(x, MeasurementSpec)])

    class FakeIngredientSpecCollection(IngredientSpecCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[IngredientSpec]:
            return iter([x for x in gemds if isinstance(x, IngredientSpec)])

    class FakeDataset(Dataset):
        def __init__(self):
            self.name = "Test Dataset"
            self.project_id = UUID("6b608f78-e341-422c-8076-35adc8828545")
            self.uid = UUID("503d7bf6-8e2d-4d29-88af-257af0d4fe4a")
            self.session = FakeSession()

        @property
        def property_templates(self) -> PropertyTemplateCollection:
            return FakePropertyTemplateCollection()

        @property
        def condition_templates(self) -> ConditionTemplateCollection:
            return FakeConditionTemplateCollection()

        @property
        def parameter_templates(self) -> ParameterTemplateCollection:
            return FakeParameterTemplateCollection()

        @property
        def process_templates(self) -> ProcessTemplateCollection:
            return FakeProcessTemplateCollection()

        @property
        def material_templates(self) -> MaterialTemplateCollection:
            return FakeMaterialTemplateCollection()

        @property
        def measurement_templates(self) -> MeasurementTemplateCollection:
            return FakeMeasurementTemplateCollection()

        @property
        def process_runs(self) -> ProcessRunCollection:
            return FakeProcessRunCollection()

        @property
        def material_runs(self) -> MaterialRunCollection:
            return FakeMaterialRunCollection()

        @property
        def measurement_runs(self) -> MeasurementRunCollection:
            return FakeMeasurementRunCollection()

        @property
        def ingredient_runs(self) -> IngredientRunCollection:
            return FakeIngredientRunCollection()

        @property
        def process_specs(self) -> ProcessSpecCollection:
            return FakeProcessSpecCollection()

        @property
        def material_specs(self) -> MaterialSpecCollection:
            return FakeMaterialSpecCollection()

        @property
        def measurement_specs(self) -> MeasurementSpecCollection:
            return FakeMeasurementSpecCollection()

        @property
        def ingredient_specs(self) -> IngredientSpecCollection:
            return FakeIngredientSpecCollection()

    return FakeDataset()


def test_wipe_dataset(fake_dataset):

    failure_resp = {"failures": [
        {
            "id":{
                "scope": "somescope",
                "id": "abcd-1234"
            },
            "cause": {
                "code": 400,
                "message": "",
                "validation_errors": [
                    {
                        "failure_message": "fail msg",
                        "failure_id": "identifier.coreid.missing"
                    }
                ]
            }
        }
    ]}
    num_objs = len([
        *fake_dataset.ingredient_runs.list_all(),
        *fake_dataset.ingredient_specs.list_all(),
        *fake_dataset.material_runs.list_all(),
        *fake_dataset.material_specs.list_all(),
        *fake_dataset.measurement_runs.list_all(),
        *fake_dataset.measurement_specs.list_all(),
        *fake_dataset.process_runs.list_all(),
        *fake_dataset.process_specs.list_all(),
    ])
    num_templates = len([
        *fake_dataset.material_templates.list_all(),
        *fake_dataset.measurement_templates.list_all(),
        *fake_dataset.process_templates.list_all(),
        # uncomment these when attribute template delete is possible
        # *fake_dataset.property_templates.list_all(),
        # *fake_dataset.condition_templates.list_all(),
        # *fake_dataset.parameter_templates.list_all(),
    ])
    
    # Clear GEMD objects only (not templates)
    responses = (failure_resp, ) * math.ceil(num_objs / DELETE_SERVICE_MAX)
    fake_dataset.session.set_responses(*responses)
    del_response = wipe_dataset(fake_dataset)
    assert len(del_response) == len(responses)

    # Clear GEMD objects AND templates
    responses = (failure_resp, ) * math.ceil((num_objs + num_templates) / DELETE_SERVICE_MAX)
    fake_dataset.session.set_responses(*responses)
    del_response = wipe_dataset(fake_dataset, delete_templates=True)
    assert len(del_response) == len(responses)
