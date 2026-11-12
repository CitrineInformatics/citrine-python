"""Tests of the object template schema."""

import warnings
from uuid import uuid4

import pytest
from gemd.entity.bounds.categorical_bounds import CategoricalBounds
from gemd.entity.bounds.integer_bounds import IntegerBounds
from gemd.entity.bounds.real_bounds import RealBounds
from gemd.entity.link_by_uid import LinkByUID

from citrine.resources.condition_template import ConditionTemplate
from citrine.resources.material_template import MaterialTemplate
from citrine.resources.measurement_template import MeasurementTemplate
from citrine.resources.parameter_template import ParameterTemplate
from citrine.resources.process_template import ProcessTemplate
from citrine.resources.property_template import PropertyTemplate


def test_object_template_serde():
    """Test serde of an object template."""
    length_template = PropertyTemplate("Length", bounds=RealBounds(2.0, 3.5, "cm"))
    sub_bounds = RealBounds(2.5, 3.0, "cm")
    color_template = PropertyTemplate("Color", bounds=CategoricalBounds(["red", "green", "blue"]))
    # Properties are a mixture of property templates and [template, bounds], pairs
    block_template = MaterialTemplate(
        "Block", properties=[[length_template, sub_bounds], color_template]
    )
    copy_template = MaterialTemplate.build(block_template.dump())
    assert copy_template == block_template

    # Tests below exercise similar code, but for measurement and process templates
    pressure_template = ConditionTemplate("pressure", bounds=RealBounds(0.1, 0.11, "MPa"))
    index_template = ParameterTemplate("index", bounds=IntegerBounds(2, 10))
    meas_template = MeasurementTemplate(
        "A measurement of length",
        properties=[length_template],
        conditions=[pressure_template],
        description="Description",
        parameters=[index_template],
        tags=["foo"],
    )
    assert MeasurementTemplate.build(meas_template.dump()) == meas_template

    proc_template = ProcessTemplate(
        "Make an object",
        parameters=[index_template],
        conditions=[pressure_template],
        allowed_labels=["Label"],
    )
    assert ProcessTemplate.build(proc_template.dump()) == proc_template

    # Attribute template/bounds pairs are normalized to tuples, matching gemd
    for template in (meas_template, proc_template, ProcessTemplate.build(proc_template.dump())):
        for pairs in (template.conditions, template.parameters):
            assert all(isinstance(pair, tuple) for pair in pairs)

    # Check that serde still works if the template is a LinkByUID
    pressure_template.uids["id"] = "12345"  # uids['id'] not populated by default
    proc_template.conditions[0] = (
        LinkByUID("id", pressure_template.uids["id"]),
        proc_template.conditions[0][1],
    )
    assert ProcessTemplate.build(proc_template.dump()) == proc_template


def test_bounds_optional():
    """Test that each object template can have passthrough bounds for any of its attributes."""

    def link():
        return LinkByUID(id=str(uuid4()), scope=str(uuid4()))

    for template_type, attribute_args in [
        (MaterialTemplate, [("properties", PropertyTemplate)]),
        (ProcessTemplate, [("conditions", ConditionTemplate), ("parameters", ParameterTemplate)]),
        (
            MeasurementTemplate,
            [
                ("properties", PropertyTemplate),
                ("conditions", ConditionTemplate),
                ("parameters", ParameterTemplate),
            ],
        ),
    ]:
        kwargs = {}
        for name, attribute_type in attribute_args:
            kwargs[name] = [
                [link(), IntegerBounds(0, 10)],
                link(),
                attribute_type("foo", bounds=IntegerBounds(0, 10)),
                (link(), None),
            ]
        template = template_type(name="foo", **kwargs)
        for name, _ in attribute_args:
            attributes = getattr(template, name)
            assert len(attributes) == 4
            for _, bounds in attributes[1:]:
                assert bounds is None
            dumped = template.dump()
            for _, bounds in dumped[name][1:]:
                assert bounds is None
            assert template_type.build(dumped) == template


def test_process_template_allowed_names_deprecated():
    """Passing allowed_names warns, and data that still carries the field loads."""
    with pytest.warns(DeprecationWarning, match="allowed_names"):
        template = ProcessTemplate("Make an object", allowed_names=["first sample"])
    assert template.allowed_names == ["first sample"]

    data = template.dump()
    assert data["allowed_names"] == ["first sample"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        copy_template = ProcessTemplate.build(data)
    assert copy_template.allowed_names == ["first sample"]


def test_process_template_without_allowed_names():
    """Omitting allowed_names emits no deprecation warning, in construction or deserialization."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        template = ProcessTemplate("Make an object", allowed_labels=["Label"])
        # gemd round-trips an unset value as an empty list
        assert ProcessTemplate("Make an object", allowed_names=[]).allowed_names == []
        data = template.dump()
        data.pop("allowed_names", None)
        copy_template = ProcessTemplate.build(data)
    assert copy_template == template
    assert copy_template.allowed_labels == ["Label"]
