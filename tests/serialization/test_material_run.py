"""Tests of the Material Run schema."""

import json
from typing import Iterable, Optional

from gemd.demo.cake import make_cake
from gemd.entity.file_link import FileLink
from gemd.entity.link_by_uid import LinkByUID
from gemd.entity.object import MaterialRun as GEMDMaterialRun
from gemd.entity.object import MaterialSpec as GEMDMaterialSpec
from gemd.entity.object import ProcessRun as GEMDProcessRun
from gemd.entity.object import ProcessSpec as GEMDProcessSpec
from gemd.json import GEMDJson

from citrine.resources.ingredient_run import IngredientRun
from citrine.resources.ingredient_spec import IngredientSpec
from citrine.resources.material_run import MaterialRun
from citrine.resources.material_spec import MaterialSpec
from citrine.resources.measurement_run import MeasurementRun
from citrine.resources.measurement_spec import MeasurementSpec
from citrine.resources.process_run import ProcessRun
from tests.utils.factories import MaterialRunDataFactory


def test_simple_deserialization():
    """Ensure that a deserialized Material Run looks sane."""
    valid_data: dict = MaterialRunDataFactory(name="Cake 1", notes=None, spec=None)
    material_run: MaterialRun = MaterialRun.build(valid_data)
    assert isinstance(material_run, MaterialRun)
    assert material_run.uids == valid_data["uids"]
    assert material_run.name == valid_data["name"]
    assert material_run.tags == valid_data["tags"]
    assert material_run.notes is None
    assert material_run.process == LinkByUID.build(valid_data["process"])
    assert material_run.sample_type == valid_data["sample_type"]
    assert material_run.template is None
    assert material_run.spec is None
    assert material_run.file_links == [
        FileLink.build(x) for x in valid_data["file_links"]
    ]


def test_serialization():
    """Ensure that a serialized Material Run looks sane."""
    valid_data: dict = MaterialRunDataFactory()
    material_run: MaterialRun = MaterialRun.build(valid_data)
    serialized = material_run.dump()
    assert serialized == valid_data


def test_process_attachment():
    """Test that a process can be attached to a material, and that the connection survives serde"""
    cake = MaterialRun("Final cake")
    cake.process = ProcessRun("Icing", uids={"id": "12345"})
    cake_data = cake.dump()

    cake_copy = MaterialRun.build(cake_data).as_dict()

    assert cake_copy["name"] == cake.name
    assert cake_copy["uids"] == cake.uids
    assert cake.process.uids["id"] == cake_copy["process"].uids["id"]

    reconstituted_cake = MaterialRun.build(cake_copy)
    assert isinstance(reconstituted_cake, MaterialRun)
    assert isinstance(reconstituted_cake.process, ProcessRun)


def test_nested_serialization():
    """Create a bunch of nested objects and make sure that nothing breaks."""

    # helper
    def make_ingredient(material: MaterialRun):
        return IngredientRun(material=material)

    icing = ProcessRun(name="Icing")
    cake = MaterialRun(name="Final cake", process=icing)

    cake.process.ingredients.append(make_ingredient(MaterialRun("Baked Cake")))
    cake.process.ingredients.append(make_ingredient(MaterialRun("Frosting")))

    baked = cake.process.ingredients[0].material
    baked.process = ProcessRun(name="Baking")
    baked.process.ingredients.append(make_ingredient(MaterialRun("Batter")))

    batter = baked.process.ingredients[0].material
    batter.process = ProcessRun(name="Mixing batter")

    batter.process.ingredients.append(make_ingredient(material=MaterialRun("Butter")))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun("Sugar")))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun("Flour")))
    batter.process.ingredients.append(make_ingredient(material=MaterialRun("Milk")))

    cake.dump()


def test_measurement_material_connection_rehydration():
    """Test that fully-linked GEMD object can be built as fully-linked Citrine-python object."""

    process_spec = GEMDProcessSpec("Transformative process")
    process = GEMDProcessRun("Transformative process", spec=process_spec)

    ending_mat_spec = GEMDMaterialSpec("ending material", process=process_spec)
    ending_mat = GEMDMaterialRun(
        "ending material", process=process, spec=ending_mat_spec
    )

    copy = MaterialRun.build(json.loads(GEMDJson().dumps(ending_mat)))
    assert isinstance(copy, MaterialRun), "copy of ending_mat should be a MaterialRun"
    assert len(copy.measurements) == 1, "copy of ending_mat should have one measurement"
    assert isinstance(copy.measurements[0], MeasurementRun), (
        "copy of ending_mat should have a measurement that is a MeasurementRun"
    )
    assert isinstance(copy.measurements[0].spec, MeasurementSpec), (
        "copy of ending_mat should have a measurement that has a spec that is a MeasurementSpec"
    )
    assert isinstance(copy.process, ProcessRun), (
        "copy of ending_mat should have a process"
    )
    assert len(copy.process.ingredients) == 1, (
        "copy of ending_mat should have a process with one ingredient"
    )
    assert isinstance(copy.spec, MaterialSpec), "copy of ending_mat should have a spec"
    assert len(copy.spec.process.ingredients) == 1, (
        "copy of ending_mat should have a spec with a process that has one ingredient"
    )
    assert isinstance(copy.process.spec.ingredients[0], IngredientSpec), (
        "copy of ending_mat should have a spec with a process that has an ingredient "
        "that is an IngredientRun"
    )

    copy_ingredient = copy.process.ingredients[0]
    assert isinstance(copy_ingredient, IngredientRun), (
        "copy of ending_mat should have a process with an ingredient that is an IngredientRun"
    )
    assert isinstance(copy_ingredient.material, MaterialRun), (
        "copy of ending_mat should have a process with an ingredient that links to a MaterialRun"
    )
    assert len(copy_ingredient.material.measurements) == 1, (
        "copy of ending_mat should have a process with an ingredient derived from a material "
        "that has one measurement performed on it"
    )
    assert isinstance(copy_ingredient.material.measurements[0], MeasurementRun), (
        "copy of ending_mat should have a process with an ingredient derived from a material "
        "that has one measurement that gets deserialized as a MeasurementRun"
    )
    assert isinstance(copy_ingredient.material.measurements[0].spec, MeasurementSpec), (
        "copy of ending_mat should have a process with an ingredient derived from a material "
        "that has one measurement that has a spec"
    )


def test_cake():
    """
    Test that the cake example from gemd can be built without modification.

    This example has complex interconnections and fully exercises the data model.
    We want to test if when such a material history is serialized and deserialized,
    all relevant logical relationships are restored -- that objects that appear
    in different parts of the material history are literally identical and not
    just copies.
    """
    gemd_cake = make_cake()
    cake = MaterialRun.build(json.loads(GEMDJson().dumps(gemd_cake)))
    assert [ingred.name for ingred in cake.process.ingredients] == [
        ingred.name for ingred in gemd_cake.process.ingredients
    ]
    assert [ingred.labels for ingred in cake.process.ingredients] == [
        ingred.labels for ingred in gemd_cake.process.ingredients
    ]
    assert gemd_cake == cake

    def _by_name(start: MaterialRun, names: Iterable[str]) -> Optional[MaterialRun]:
        if isinstance(names, str):
            names = [names]
        while names:
            target = names.pop(0)
            start = next(
                (i.material for i in start.process.ingredients if i.name == target),
                None,
            )
            if start is None:
                return None
        return start

    by_cake = _by_name(cake, ["baked cake", "batter", "wet ingredients", "butter"])
    by_frosting = _by_name(cake, ["frosting", "butter"])
    assert by_cake is by_frosting  # Same literal object
    assert (
        _by_name(gemd_cake, ["frosting", "butter"]) is not by_frosting
    )  # Same literal object
