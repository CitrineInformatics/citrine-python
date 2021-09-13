import pkg_resources

from citrine.seeding.parse_csv import guess_attribute_templates, guess_object_templates, objectify_rows, \
    is_binary_series, is_binary_attribute, fill_binary, attribute_template_to_builder

from gemd.json import GEMDJson
from gemd.entity.template import PropertyTemplate, ConditionTemplate, ParameterTemplate, \
    MaterialTemplate, MeasurementTemplate, ProcessTemplate
from gemd.entity.bounds import IntegerBounds, RealBounds, CategoricalBounds, CompositionBounds, \
    MolecularStructureBounds
from gemd.entity.attribute import Property, Condition, Parameter
from gemd.entity.value import NominalCategorical, NominalReal, NominalInteger, EmpiricalFormula, \
    Smiles, InChI

import pandas as pd
import numpy as np

from pytest import raises, warns, mark


def test_binaries():
    """Test the binary variable tools."""
    value_checks = {
        0: True,
        1: True,
        "0": True,
        "1": True,
        "0.000000": True,
        "1.": True,
        np.nan: True,  # An empty column could plausibly be binary
        -1: False,
        2: False,
        1e-32: False,
        "0.00001": False,
        0.00001: False,
        "0.000.0": False,
    }
    for k, v in value_checks.items():
        assert is_binary_series(pd.Series(k)) == v, f"is_binary_series({k}) returned {v}"

    tmpl1 = PropertyTemplate(
        name="Template 1",
        bounds=IntegerBounds(0, 1)
    )
    assert is_binary_attribute(tmpl1), "Bounds expected to pass is_binary_attribute"
    tmpl2 = PropertyTemplate(
        name="Template 2",
        bounds=IntegerBounds(0, 2)
    )
    assert not is_binary_attribute(tmpl2), "Bounds not expected to pass is_binary_attribute"
    tmpl3 = ConditionTemplate(
        name="Template 3",
        bounds=RealBounds(0, 1, default_units='km')
    )
    assert(not is_binary_attribute(tmpl3)), "Bounds not expected to pass is_binary_attribute"

    binary_df = fill_binary(value=2.0, df=pd.DataFrame(
        data={
            "bin1": [0, 1, np.nan],
            "bin2": ["0", "1", np.nan],
            "bin3": [False, True, np.nan],
            "bin4": [np.nan, np.nan, np.nan],
            "not_bin1": [2, 1, np.nan],
        }
    ))
    for col in [f"bin{i}" for i in range(1,5)]:
        assert len(binary_df[col].dropna()) == 3, f"NaNs were not dropped from {col}"
    assert len(binary_df["not_bin1"].dropna()) == 2, "NaNs were dropped from not_bin1"


def test_attribute_template_to_builder():
    """Verify all types propagate as expected."""
    real_prop_tmpl = PropertyTemplate(
        name="Real Property",
        bounds=RealBounds(0, 1, "lbs")
    )
    real_prop = attribute_template_to_builder(real_prop_tmpl)(5.2)
    assert isinstance(real_prop, Property), \
        f"attribute_template_to_builder({real_prop_tmpl.name}) returned the wrong type"
    assert isinstance(real_prop.value, NominalReal), \
        f"attribute_template_to_builder({real_prop_tmpl.name}) returned the wrong type"
    assert real_prop.value.nominal == 5.2, \
        f"attribute_template_to_builder({real_prop_tmpl.name}) returned the wrong value ({real_prop.value.nominal})"
    assert real_prop.value.units == real_prop_tmpl.bounds.default_units, \
        f"attribute_template_to_builder({real_prop_tmpl.name}) returned the wrong units ({real_prop.value.units})"

    cat_cond_tmpl = ConditionTemplate(
        name="Categorical Condition",
        bounds=CategoricalBounds(['at', 'bat', 'cat'])
    )
    cat_cond = attribute_template_to_builder(cat_cond_tmpl)('cat')
    assert isinstance(cat_cond, Condition), \
        f"attribute_template_to_builder({cat_cond_tmpl.name}) returned the wrong type"
    assert isinstance(cat_cond.value, NominalCategorical), \
        f"attribute_template_to_builder({cat_cond_tmpl.name}) returned the wrong type"
    assert cat_cond.value.category == 'cat', \
        f"attribute_template_to_builder({cat_cond_tmpl.name}) returned the wrong value ({cat_cond.value.category})"

    int_param_tmpl = ParameterTemplate(
        name="Integer Parameter",
        bounds=IntegerBounds(0, 2)
    )
    int_param = attribute_template_to_builder(int_param_tmpl)(1)
    assert isinstance(int_param, Parameter), \
        f"attribute_template_to_builder({int_param_tmpl.name}) returned the wrong type"
    assert isinstance(int_param.value, NominalInteger), \
        f"attribute_template_to_builder({int_param_tmpl.name}) returned the wrong type"
    assert int_param.value.nominal == 1, \
        f"attribute_template_to_builder({int_param_tmpl.name}) returned the wrong value ({int_param.value.nominal})"

    comp_prop_tmpl = PropertyTemplate(
        name="Composition Property",
        bounds=CompositionBounds(EmpiricalFormula.all_elements())
    )
    comp_prop = attribute_template_to_builder(comp_prop_tmpl)('NaCl')
    assert isinstance(comp_prop, Property), \
        f"attribute_template_to_builder({comp_prop_tmpl.name}) returned the wrong type"
    assert isinstance(comp_prop.value, EmpiricalFormula), \
        f"attribute_template_to_builder({comp_prop_tmpl.name}) returned the wrong type"
    assert comp_prop.value.formula == 'NaCl', \
        f"attribute_template_to_builder({comp_prop_tmpl.name}) returned the wrong value ({comp_prop.value.formula})"

    struct_prop_tmpl = PropertyTemplate(
        name="Molecular Structure Property",
        bounds=MolecularStructureBounds()
    )
    inchi_prop = attribute_template_to_builder(struct_prop_tmpl)('InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H')
    assert isinstance(inchi_prop, Property), \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong type"
    assert isinstance(inchi_prop.value, InChI), \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong type"
    assert inchi_prop.value.inchi == 'InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H', \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong value ({inchi_prop.value.inchi})"

    smiles_prop = attribute_template_to_builder(struct_prop_tmpl)('C1=CC=CC=C1')
    assert isinstance(smiles_prop, Property), \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong type"
    assert isinstance(smiles_prop.value, Smiles), \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong type"
    assert smiles_prop.value.smiles == 'C1=CC=CC=C1', \
        f"attribute_template_to_builder({struct_prop_tmpl.name}) returned the wrong value ({smiles_prop.value.smiles})"

    with raises(TypeError):
        attribute_template_to_builder(MaterialTemplate(name='Error'))


@mark.filterwarnings("ignore:Skipping column")
def test_ingest():
    """Test the parse_csv ingest utilities."""
    file = pkg_resources.resource_filename("tests", "seeding/test.csv")
    df = pd.read_csv(file)

    attr_tmpls = guess_attribute_templates("attr-test", df)
    # Note that one "PROPERTY" column is left intentionally blank
    assert len(attr_tmpls) == len([x for x in df.columns if "PROPERTY" in x or "DETAIL" in x]) - 1

    obj_tmpls = guess_object_templates("obj-test", df, attr_tmpls=attr_tmpls)
    assert len([x for x in obj_tmpls.values() if isinstance(x, MaterialTemplate)]) \
        == len(df["CLASSIFICATION: component type"].unique()), "Material type count mismatch"
    assert len([x for x in obj_tmpls.values() if isinstance(x, ProcessTemplate)]) \
        == len(df["PREPARATION STEP NAME"].unique()), "Process type count mismatch"
    expected_msr = 0  # Count the number of different availability signatures
    prop_cols = [col for col in df if "PROPERTY" in col]
    for i, coli in enumerate(prop_cols):
        if df[coli].isnull().all():
            continue  # Skip empties
        for colj in prop_cols[i+1:]:
            if (df[coli].notnull() == df[colj].notnull()).all():
                break
        else:
            expected_msr += 1
    assert expected_msr == len([x for x in obj_tmpls.values() if isinstance(x, MeasurementTemplate)]), \
        "Measurement cluster count mismatch"

    objects = objectify_rows("obj-test", df, attr_tmpls=attr_tmpls, obj_tmpls=obj_tmpls)
    assert len(objects) == len(df), "Didn't get one object per row"

    json = GEMDJson().dumps(objects)

    str_slice = df.select_dtypes(include="object")
    assert all(
        str_slice.isnull() | str_slice.applymap(lambda x: str(x) in json)
    ), "Not all strings from the dataframe were included"

    # Try again, but all just threading through
    assert len(guess_object_templates("obj-test-2", df)) == len(obj_tmpls), "guess_object_templates didn't replicate"
    assert len(objectify_rows("obj-test-2", df)) == len(objects), "objectify_rows didn't replicate"


def test_bad_inputs():
    with raises(ValueError):
        file = pkg_resources.resource_filename("tests", "seeding/object_collision.csv")
        df = pd.read_csv(file)
        guess_object_templates("attr-test", df)

    with raises(ValueError):
        file = pkg_resources.resource_filename("tests", "seeding/object_collision.csv")
        df = pd.read_csv(file)
        df.reindex(columns=[
            'IDENTIFIER: name',
            'PREPARATION STEP NAME',
            'CLASSIFICATION: component type',
        ])
        guess_object_templates("attr-test", df)

    with raises(ValueError):
        file = pkg_resources.resource_filename("tests", "seeding/bad_column.csv")
        df = pd.read_csv(file)
        guess_attribute_templates("attr-test", df)

    with warns(UserWarning):
        file = pkg_resources.resource_filename("tests", "seeding/empty_column.csv")
        df = pd.read_csv(file)
        result = guess_attribute_templates("attr-test", df)
        assert len(result) == 0, "Empty didn't return empty"

    with raises(ValueError):
        file = pkg_resources.resource_filename("tests", "seeding/failed_test.csv")
        df = pd.read_csv(file)
        objectify_rows("obj-test", df)
