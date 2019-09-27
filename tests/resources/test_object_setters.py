"""Test that setting objects in citrine-python activates the setter logic in taurus."""

import pytest

from taurus.entity.value.discrete_categorical import DiscreteCategorical
from citrine.attributes.property import Property
from citrine.resources.process_run import ProcessRun
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.measurement_run import MeasurementRun
from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.ingredient_spec import IngredientSpec


def test_soft_process_material_attachment():
    """Test that soft attachments are formed from process to output material"""
    baking = ProcessRun("Bake a cake")
    cake = MaterialRun("A cake", process=baking)
    assert baking.output_material == cake


def test_soft_measurement_material_attachment():
    """Test that soft attachments are formed from materials to measurements."""
    cake = MaterialRun("A cake")
    smell_test = MeasurementRun("use your nose", material=cake, properties=[
        Property(name="Smell",  value=DiscreteCategorical("yummy"))])
    taste_test = MeasurementRun("taste", material=cake)
    assert cake.measurements == [smell_test, taste_test]


def test_soft_process_ingredient_attachment():
    """Test that soft attachments are formed from process to ingredients"""
    vinegar = MaterialSpec("vinegar")
    baking_soda = MaterialSpec("baking soda")
    eruption = ProcessSpec("Volcano eruption")
    vinegar_sample = IngredientSpec("a bit of vinegar", material=vinegar, process=eruption)
    baking_soda_sample = IngredientSpec("a bit of NaOh", material=baking_soda)
    baking_soda_sample.process = eruption
    assert set(eruption.ingredients) == {vinegar_sample, baking_soda_sample}, \
        "Creating an ingredient for a process did not auto-populate that process's ingredient list"


def test_object_pointer_serde():
    """Test that an object can point to another object, and that this survives serde."""
    baking = ProcessRun("Bake a cake")
    cake = MaterialRun("A cake", process=baking)
    reconstituted_cake = MaterialRun.build(cake.dump())
    assert isinstance(reconstituted_cake.process, ProcessRun)
    assert isinstance(reconstituted_cake.process.output_material, MaterialRun)


def test_object_validation():
    """Test that an object pointing to another object is validated."""
    meas = MeasurementRun("A measurement")
    with pytest.raises(TypeError):
        MaterialRun("A cake", process=meas)


def test_list_validation():
    """Test that lists are validated by taurus."""
    mat = MaterialRun("A material")
    with pytest.raises(TypeError):
        # labels must be a list of string, but contains an int
        IngredientRun(material=mat, labels=["Label 1", 17], name="foo")

    ingredient = IngredientRun(material=mat, labels=["Label 1", "label 2"], name="foo")
    with pytest.raises(TypeError):
        # cannot append an int to a list of strings
        ingredient.labels.append(17)

    with pytest.raises(TypeError):
        # list of conditions cannot contain a property
        MeasurementRun("A measurement", conditions=[Property("not a condition")])
