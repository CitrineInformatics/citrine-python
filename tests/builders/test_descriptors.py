from typing import Iterator

import pytest
from gemd.entity.bounds import RealBounds, CategoricalBounds, MolecularStructureBounds, \
    CompositionBounds, IntegerBounds
from gemd.entity.bounds.base_bounds import BaseBounds
from gemd.entity.template import PropertyTemplate, ConditionTemplate, ParameterTemplate
from gemd.entity.value import EmpiricalFormula

from citrine.builders.descriptors import PlatformVocabulary, template_to_descriptor, \
    NoEquivalentDescriptorError
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, \
    MolecularStructureDescriptor, ChemicalFormulaDescriptor
from citrine.resources.condition_template import ConditionTemplateCollection
from citrine.resources.parameter_template import ParameterTemplateCollection
from citrine.resources.project import Project
from citrine.resources.property_template import PropertyTemplateCollection

density_desc = RealDescriptor("density", lower_bound=0, upper_bound=100, units="gram / centimeter ** 3")
pressure_desc = RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")


@pytest.fixture()
def fake_project():
    """Fake project that serves templates from template collection's list_all method."""
    templates = [
        PropertyTemplate("density", bounds=RealBounds(lower_bound=0, upper_bound=100, default_units="g / cm^3"), uids={"my_scope": "density"}),
        ConditionTemplate("volume", bounds=IntegerBounds(lower_bound=0, upper_bound=11), uids={"my_scope": "volume"}),
        ParameterTemplate("speed", bounds=CategoricalBounds(categories=["slow", "fast"]), uids={})
    ]

    class FakePropertyTemplateCollection(PropertyTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[PropertyTemplate]:
            return iter([x for x in templates if isinstance(x, PropertyTemplate)])

    class FakeConditionTemplateCollection(ConditionTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ConditionTemplate]:
            return iter([x for x in templates if isinstance(x, ConditionTemplate)])

    class FakeParameterTemplateCollection(ParameterTemplateCollection):
        def __init__(self):
            pass

        def list_all(self, forward: bool = True, per_page: int = 100) -> Iterator[ParameterTemplate]:
            return iter([x for x in templates if isinstance(x, ParameterTemplate)])

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

    return FakeProject()


def test_valid_template_conversions():
    expected = [
        (
            PropertyTemplate(name="density", bounds=RealBounds(lower_bound=0, upper_bound=100, default_units="g/cm^3")),
            density_desc
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
            PropertyTemplate(name="formula", bounds=CompositionBounds(components=EmpiricalFormula.all_elements())),
            ChemicalFormulaDescriptor(key="formula")
        )
    ]

    for tmpl, desc in expected:
        assert template_to_descriptor(tmpl) == desc


def test_invalid_template_conversions():
    with pytest.raises(NoEquivalentDescriptorError):
        template_to_descriptor(
            ConditionTemplate("foo", bounds=IntegerBounds(lower_bound=0, upper_bound=1))
        )

    with pytest.raises(NoEquivalentDescriptorError):
        template_to_descriptor(
            PropertyTemplate("mixture", bounds=CompositionBounds(components=["sugar", "spice"]))
        )

    class DummyBounds(BaseBounds):
        """Fake bounds to test unrecognized bounds."""

        def contains(self, bounds):
            return False

    with pytest.raises(ValueError):
        template_to_descriptor(
            ParameterTemplate("dummy", bounds=DummyBounds())
        )


def test_dict_behavior():
    entries = {
        "density": RealDescriptor("density", lower_bound=0, upper_bound=100, units="g/cm^3"),
        "pressure": RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")
    }

    v = PlatformVocabulary(entries)

    assert len(v) == 2
    assert set(v) == {"density", "pressure"}
    assert v["density"] == entries["density"]
    assert v["pressure"] == entries["pressure"]


def test_from_template(fake_project: Project):
    """Test that only correct scopes and bounds are loaded from templates."""
    v = PlatformVocabulary.from_templates(fake_project, scope="my_scope")

    # no volume since it is an integer, no speed since it doesn't have the right scope
    assert len(v) == 1
    assert list(v) == ["density"]
    assert v["density"] == density_desc
