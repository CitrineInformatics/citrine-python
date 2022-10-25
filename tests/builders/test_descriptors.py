from uuid import uuid4, UUID
from typing import Iterator, Union
import pytest
import mock

from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.value import EmpiricalFormula
from gemd.entity.attribute import Condition, Property, Parameter
from gemd.entity.value import NominalReal, NominalInteger, NominalCategorical
from gemd.entity.template import (
    ConditionTemplate, PropertyTemplate, ParameterTemplate,
    MaterialTemplate, MeasurementTemplate, ProcessTemplate
)
from gemd.entity.object import (
    MaterialSpec, MaterialRun, ProcessSpec, ProcessRun,
    MeasurementSpec, MeasurementRun
)
from gemd.entity.bounds import (
    RealBounds, CategoricalBounds, MolecularStructureBounds,
    CompositionBounds, IntegerBounds
)

from citrine.builders.descriptors import PlatformVocabulary, template_to_descriptor, \
    NoEquivalentDescriptorError
from citrine.informatics.descriptors import RealDescriptor, IntegerDescriptor, \
    CategoricalDescriptor, MolecularStructureDescriptor, ChemicalFormulaDescriptor
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.material_run import MaterialRunCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.project import Project
from citrine.resources.property_template import PropertyTemplateCollection

from citrine.builders.auto_configure import AutoConfigureMode


density_desc = RealDescriptor("density", lower_bound=0, upper_bound=100, units="gram / centimeter ** 3")
count_desc = IntegerDescriptor("count", lower_bound=0, upper_bound=100)
pressure_desc = RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")


@pytest.fixture()
def fake_project():
    """Fake project that serves templates from template collection's list method."""
    attributes = [
        ConditionTemplate("volume", bounds=IntegerBounds(lower_bound=0, upper_bound=11), uids={"my_scope": "volume"}),
        ParameterTemplate("speed", bounds=CategoricalBounds(categories=["slow", "fast"]), uids={}),
        PropertyTemplate("density", bounds=RealBounds(lower_bound=0, upper_bound=100, default_units="g / cm^3"), uids={"my_scope": "density"})
    ]

    values = [
        Condition('volume', template=attributes[0], value=NominalInteger(nominal=4)),
        Parameter('speed', template=attributes[1], value=NominalCategorical(category='slow')),
        Property('density', template=attributes[2], value=NominalReal(nominal=50.0, units=attributes[2].bounds.default_units))
    ]

    # Object templates
    mt = MaterialTemplate('Material')
    pt = ProcessTemplate('Processing', conditions=[attributes[0]], parameters=[attributes[1]])
    mst = MeasurementTemplate('Measurement', properties=[attributes[2]])

    # Specs
    ps = ProcessSpec(name=pt.name, template=pt)
    mss = MeasurementSpec(name=mst.name, template=mst)
    ms = MaterialSpec(name=mt.name, process=ps, template=mt)

    # Runs
    pr = ProcessRun(name=ps.name, spec=ps,
                    conditions=[values[0]], parameters=[values[1]])

    history = MaterialRun(name=ms.name, process=pr, spec=ms)
    msr = MeasurementRun(name=mss.name, spec=mss, material=history,
                         properties=[values[2]])
    history.measurements.append(msr)

    class FakePropertyTemplateCollection(PropertyTemplateCollection):
        def __init__(self):
            pass

        def list(self, forward: bool = True, per_page: int = 100) -> Iterator[PropertyTemplate]:
            return iter([x for x in attributes if isinstance(x, PropertyTemplate)])

    class FakeConditionTemplateCollection(ConditionTemplateCollection):
        def __init__(self):
            pass

        def list(self, forward: bool = True, per_page: int = 100) -> Iterator[ConditionTemplate]:
            return iter([x for x in attributes if isinstance(x, ConditionTemplate)])

    class FakeParameterTemplateCollection(ParameterTemplateCollection):
        def __init__(self):
            pass

        def list(self, forward: bool = True, per_page: int = 100) -> Iterator[ParameterTemplate]:
            return iter([x for x in attributes if isinstance(x, ParameterTemplate)])

    class FakeMaterialRunCollection(MaterialRunCollection):
        def __init__(self):
            pass

        def get_history(self, *, id: Union[str, UUID, LinkByUID, MaterialRun]) -> MaterialRun:
            return history

    class FakeProject(Project):
        def __init__(self):
            pass

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
        def material_runs(self) -> MaterialRunCollection:
            return FakeMaterialRunCollection()

    return FakeProject()


def test_valid_template_conversions():
    expected = [
        (
            PropertyTemplate(name="density", bounds=RealBounds(
                lower_bound=0, upper_bound=100, default_units="g/cm^3")),
            density_desc
        ),
        (
            PropertyTemplate(name="count", bounds=IntegerBounds(
                lower_bound=0, upper_bound=100)), count_desc
        ),
        (
            ConditionTemplate(name="speed", bounds=CategoricalBounds(categories=["low", "high"])),
            CategoricalDescriptor(key="speed", categories=["low", "high"])
        ),
        (
            ParameterTemplate(name="solvent", bounds=MolecularStructureBounds()),
            MolecularStructureDescriptor(key="solvent")
        ),
        (
            PropertyTemplate(name="formula", bounds=CompositionBounds(
                components=EmpiricalFormula.all_elements())),
            ChemicalFormulaDescriptor(key="formula")
        )
    ]

    for tmpl, desc in expected:
        assert template_to_descriptor(tmpl) == desc


def test_invalid_template_conversions():
    with pytest.raises(NoEquivalentDescriptorError):
        template_to_descriptor(
            PropertyTemplate("mixture", bounds=CompositionBounds(components=["sugar", "spice"]))
        )

    class DummyBounds(BaseBounds):
        """Fake bounds to test unrecognized bounds."""

        def contains(self, bounds):
            return False

        def union(self, *others):
            return self

        def update(self):
            pass

    with pytest.raises(ValueError):
        template_to_descriptor(
            ParameterTemplate("dummy", bounds=DummyBounds())
        )


def test_dict_behavior():
    entries = {
        "density": RealDescriptor("density", lower_bound=0, upper_bound=100, units="g/cm^3"),
        "pressure": RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")
    }

    v = PlatformVocabulary(entries=entries)

    assert len(v) == 2
    assert set(v) == {"density", "pressure"}
    assert v["density"] == entries["density"]
    assert v["pressure"] == entries["pressure"]


def test_from_template(fake_project: Project):
    """Test that only correct scopes and bounds are loaded from templates."""
    v = PlatformVocabulary.from_templates(project=fake_project, scope="my_scope")

    # no speed since it doesn't have the right scope
    assert len(v) == 2
    assert list(v) == ["density", "volume"]
    assert v["density"] == density_desc

    # templates that raise NoEquivalentDescriptorError are skipped, mainly for test coverage
    with mock.patch("citrine.builders.descriptors.template_to_descriptor") as mock_template_to_descriptor:
        mock_template_to_descriptor.side_effect = NoEquivalentDescriptorError
        PlatformVocabulary.from_templates(project=fake_project, scope="my_scope")
        mock_template_to_descriptor.assert_called()


def test_from_material(fake_project: Project):
    """Test that correct descriptors and keys are extracted from history."""
    sample_mr = uuid4()  # Just a random UUID
    v1 = PlatformVocabulary.from_material(
        project=fake_project,
        material=sample_mr,
        mode=AutoConfigureMode.PLAIN,
        full_history=True
    )

    density_desc_plain = RealDescriptor(
        "Measurement~density", lower_bound=0, upper_bound=100, units="gram / centimeter ** 3")
    assert len(v1) == 3
    assert list(v1) == ['Processing~volume', 'Processing~speed', 'Measurement~density']
    assert v1['Measurement~density'] == density_desc_plain

    # Same length for sample history
    v2 = PlatformVocabulary.from_material(
        project=fake_project,
        material=sample_mr,
        mode=AutoConfigureMode.PLAIN,
        full_history=False
    )
    assert len(v1) == len(v2)

    # Raise on not passing enum option
    with pytest.raises(TypeError):
        PlatformVocabulary.from_material(
            project=fake_project,
            material=sample_mr,
            mode='BAD MODE CHOICE'
        )

    # templates that raise NoEquivalentDescriptorError are skipped, mainly for test coverage
    with mock.patch("citrine.builders.descriptors.template_to_descriptor") as mock_template_to_descriptor:
        mock_template_to_descriptor.side_effect = NoEquivalentDescriptorError
        PlatformVocabulary.from_material(
            project=fake_project,
            material=sample_mr,
            mode=AutoConfigureMode.PLAIN,
            full_history=True
        )
        mock_template_to_descriptor.assert_called()
