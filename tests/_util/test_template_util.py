from citrine._utils.template_util import make_attribute_table
from gemd.entity.object import *
from gemd.entity.attribute import *
from gemd.entity.value import *
from gemd.entity.link_by_uid import LinkByUID
import pandas as pd

def _make_list_of_gems():
    faux_gems = [
        ProcessSpec(
            name = "hello world",
            parameters = [
                Parameter(
                    name = "param 1",
                    value = NominalReal(nominal=4.2, units="g")
                ),
                Parameter(
                    name = "param 2",
                    value = NominalCategorical(category="foo")
                ),
                Parameter(
                    name = "attr 1",
                    value = InChI(inchi="InChI=1S/C8H10N4O2/c1-10-4-9-6-5(10)7(13)12(3)8(14)11(6)2/h4H,1-3H3")
                )
            ],
            conditions = [
                Condition(
                    name = "cond 1",
                    value = NormalReal(mean=4, std=0.5, units="")
                )
            ]
        ),
        IngredientSpec(
            name = "I shouldn't be a row",
            material=LinkByUID(scope = "faux", id = "abcde"),
            process=LinkByUID(scope = "foo", id = "bar")
        ),
        ProcessRun(
            name = "process 1",
            spec = LinkByUID(scope = "faux", id = "id"),
            parameters = [
                Parameter(
                    name = "param 1",
                    value = NormalReal(mean=4.2, std = 0.1, units="g")
                ),
                Parameter(
                    name = "param 3",
                    value = NominalCategorical(category="bar")
                )
            ],
            conditions = [
                Condition(
                    name = "cond 1",
                    value = NormalReal(mean=4, std=0.5, units="")
                ),
                Condition(
                    name = "cond 2",
                    value = NominalCategorical(category="hi")
                ),
                Condition(
                    name = "attr 1",
                    value = InChI(inchi="InChI=1S/C34H34N4O4.Fe/c1-7-21-17(3)25-13-26-19(5)23(9-11-33(39)40)31(37-26)16-32-24(10-12-34(41)42)20(6)28(38-32)15-30-22(8-2)18(4)27(36-30)14-29(21)35-25;/h7-8,13-16H,1-2,9-12H2,3-6H3,(H4,35,36,37,38,39,40,41,42);/q;+2/p-2")
                ),
            ]
        ),
        MaterialSpec(
            name = "material 1",
            process = LinkByUID(scope = "faux 2", id = "id2"),
            properties=[
                PropertyAndConditions(
                    property=Property(
                        name = "prop 1",
                        value = NormalReal(mean=100, std=10, units="g/cm**3")
                    ),
                    conditions=[
                        Condition(
                        name = "cond 2",
                        value = NominalCategorical(category="hi")
                        )
                    ]
                ),
                PropertyAndConditions(
                    property=Property(
                        name = "prop 2",
                        value = NominalReal(nominal=33, units="1/lb")
                    ),
                    conditions=[
                        Condition(
                        name = "cond 3",
                        value = NominalCategorical(category="citrine")
                        )
                    ]
                ),
            ]
        ),
        MeasurementSpec(
            name = "meas spec 1",
            parameters = [
                Parameter(
                    name = "param 1",
                    value = NominalReal(nominal=2.2, units="kg")
                ),
                Parameter(
                    name = "param 2",
                    value = NominalCategorical(category="bar")
                )
            ],
        ),
        MeasurementRun(
            name = "meas run 1",
            spec = LinkByUID(scope="another fake scope", id = "another fake id"),
            properties=[
                Property(
                    name = "prop 1",
                    value=NominalReal(nominal=4.1, units="")
                )
            ]
        )
    ]
    return faux_gems

def test_attribute_alignment():
    df = make_attribute_table(_make_list_of_gems())
    assert isinstance(df.iloc[0,3], NominalReal)
    assert isinstance(df.iloc[1,3], NormalReal)
    assert isinstance(df.iloc[3,3], NominalReal)
    assert isinstance(df.iloc[0,5], InChI)
    assert pd.isnull(df.iloc[1,5])
    assert df.shape == (5,12)
