"""Test that templates show expected behavior."""
import pytest
from uuid import uuid4

from citrine.resources.material_template import MaterialTemplate
from citrine.resources.measurement_template import MeasurementTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.process_spec import ProcessSpec
from citrine.resources.property_template import PropertyTemplate, PropertyTemplateCollection
from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.exceptions import BadRequest
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.bounds.categorical_bounds import CategoricalBounds
from gemd.entity.value.nominal_real import NominalReal
from gemd.entity.attribute.condition import Condition

from tests.utils.session import FakeSession, FakeCall


def test_object_template_validation():
    """Test that attribute templates are validated against given bounds."""
    length_template = PropertyTemplate("Length", bounds=RealBounds(2.0, 3.5, 'cm'))
    dial_template = ConditionTemplate("dial", bounds=IntegerBounds(0, 5))
    color_template = ParameterTemplate("Color", bounds=CategoricalBounds(["red", "green", "blue"]))

    with pytest.raises(TypeError):
        MaterialTemplate()

    with pytest.raises(ValueError):
        MaterialTemplate("Block", properties=[[length_template, RealBounds(3.0, 4.0, 'cm')]])

    with pytest.raises(ValueError):
        ProcessTemplate("a process", conditions=[[color_template, CategoricalBounds(["zz"])]])
        
    with pytest.raises(ValueError):
        MeasurementTemplate("A measurement", parameters=[[dial_template, IntegerBounds(-3, -1)]])


def test_template_assignment():
    """Test that an object and its attributes can both be assigned templates."""
    humidity_template = ConditionTemplate("Humidity", bounds=RealBounds(0.5, 0.75, ""))
    template = ProcessTemplate("Dry", conditions=[[humidity_template, RealBounds(0.5, 0.65, "")]])
    ProcessSpec("Dry a polymer", template=template, conditions=[
        Condition("Humidity", value=NominalReal(0.6, ""), template=humidity_template)])


def test_automatic_async_update():
    """Update on an object that requires an asynchronous check smoothly transitions to async_update."""
    session = FakeSession()
    collection = PropertyTemplateCollection(project_id=uuid4(), dataset_id=uuid4(), session=session)
    this_id = str(uuid4())
    template = PropertyTemplate("dummy template", bounds=RealBounds(0.0, 0.5, ''), uids={'id': this_id})

    session.set_responses(
        BadRequest(""),  # Attempted POST throws BadRequest because, for example, the template bounds are being narrowed.
        {"job_id": str(uuid4())},  # Call async route, returning a job_id.
        {"job_type": "", "status": "Success", "tasks": []},  # Check job status, it succeeded.
        template.dump()  # Get the resource.
    )
    new_template = collection.update(template)
    assert new_template == template  # Check that resource is returned.
    # First call should be an attempt to POST the resource
    assert session.calls[0].method == "POST"
    assert session.calls[0].path == f"projects/{collection.project_id}/datasets/{collection.dataset_id}/property-templates"
    # Second call should be a PUT to the async route
    assert session.calls[1].method == "PUT"
    assert session.calls[1].path == f"projects/{collection.project_id}/datasets/{collection.dataset_id}/property-templates/id/{this_id}/async"
    # Last call should get the resource
    assert session.last_call.method == "GET"
    assert session.last_call.path == f"projects/{collection.project_id}/datasets/{collection.dataset_id}/property-templates/id/{this_id}"


def test_process_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.process_template import ProcessTemplate as CitrineProcessTemplate
    from gemd.entity.template import ProcessTemplate as GEMDProcessTemplate

    gemd_obj = GEMDProcessTemplate(
        name="My Name",
        tags=["tag!"]
    )
    citrine_obj = CitrineProcessTemplate(
        name="My Name",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_material_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.material_template import MaterialTemplate as CitrineMaterialTemplate
    from gemd.entity.template import MaterialTemplate as GEMDMaterialTemplate

    gemd_obj = GEMDMaterialTemplate(
        name="My Name",
        tags=["tag!"]
    )
    citrine_obj = CitrineMaterialTemplate(
        name="My Name",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_measurement_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.measurement_template import MeasurementTemplate as CitrineMeasurementTemplate
    from gemd.entity.template import MeasurementTemplate as GEMDMeasurementTemplate

    gemd_obj = GEMDMeasurementTemplate(
        name="My Name",
        tags=["tag!"]
    )
    citrine_obj = CitrineMeasurementTemplate(
        name="My Name",
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_condition_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.condition_template import ConditionTemplate as CitrineConditionTemplate
    from gemd.entity.template import ConditionTemplate as GEMDConditionTemplate

    gemd_obj = GEMDConditionTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    citrine_obj = CitrineConditionTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_parameter_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.parameter_template import ParameterTemplate as CitrineParameterTemplate
    from gemd.entity.template import ParameterTemplate as GEMDParameterTemplate

    gemd_obj = GEMDParameterTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    citrine_obj = CitrineParameterTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"


def test_property_template_equals():
    """Test basic equality.  Complex relationships are tested in test_material_run.test_deep_equals()."""
    from citrine.resources.property_template import PropertyTemplate as CitrinePropertyTemplate
    from gemd.entity.template import PropertyTemplate as GEMDPropertyTemplate

    gemd_obj = GEMDPropertyTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    citrine_obj = CitrinePropertyTemplate(
        name="My Name",
        bounds=CategoricalBounds(categories=["1"]),
        tags=["tag!"]
    )
    assert gemd_obj == citrine_obj, "GEMD/Citrine equivalence"
    citrine_obj.name = "Something else"
    assert gemd_obj != citrine_obj, "GEMD/Citrine detects difference"
