import pytest
from gemd.entity.bounds import RealBounds, CategoricalBounds, MolecularStructureBounds, \
    CompositionBounds, IntegerBounds
from gemd.entity.template import PropertyTemplate, ConditionTemplate, ParameterTemplate
from gemd.entity.value import EmpiricalFormula

from citrine.builders.descriptors import PlatformVocabulary, template_to_descriptor
from citrine.informatics.descriptors import RealDescriptor, CategoricalDescriptor, \
    MolecularStructureDescriptor, ChemicalFormulaDescriptor

density_desc = RealDescriptor("density", lower_bound=0, upper_bound=100, units="gram / centimeter ** 3")
pressure_desc = RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")


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
    with pytest.raises(ValueError):
        template_to_descriptor(
            ConditionTemplate("foo", bounds=IntegerBounds(lower_bound=0, upper_bound=1))
        )

    with pytest.raises(ValueError):
        template_to_descriptor(
            PropertyTemplate("mixture", bounds=CompositionBounds(components=["sugar", "spice"]))
        )


def test_dict_behavior():
    entries = {
        "density": RealDescriptor("density", lower_bound=0, upper_bound=100, units="g/cm^3"),
        "pressure": RealDescriptor("pressure", lower_bound=0, upper_bound=10000, units="GPa")
    }

    v = PlatformVocabulary(entries)

    assert len(v) == 2
    assert list(v) == ["density", "pressure"]
    assert v["density"] == entries["density"]
    assert v["pressure"] == entries["pressure"]