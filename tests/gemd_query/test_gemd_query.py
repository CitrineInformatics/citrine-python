from uuid import uuid4
import pytest

from citrine.gemd_queries.criteria import PropertiesCriteria
from citrine.gemd_queries.filter import AllRealFilter
from citrine.gemd_queries.gemd_query import GemdQuery

from tests.utils.factories import GemdQueryDataFactory


def test_gemd_query_version():
    valid = GemdQueryDataFactory()
    assert GemdQuery.build(valid) is not None

    invalid = GemdQueryDataFactory()
    invalid['schema_version'] = 2
    with pytest.raises(ValueError):
        GemdQuery.build(invalid)


def test_criteria_rebuild():
    value_filter = AllRealFilter()
    value_filter.unit = 'm'
    value_filter.lower = 0
    value_filter.upper = 1

    crit = PropertiesCriteria()
    crit.property_templates_filter = {uuid4()}
    crit.value_type_filter = value_filter

    query = GemdQuery()
    query.criteria.append(crit)
    query.datasets.add(uuid4())
    query.object_types = {'material_run'}

    query_copy = GemdQuery.build(query.dump())

    assert len(query.criteria) == len(query_copy.criteria)
    assert query.criteria[0].property_templates_filter == query_copy.criteria[0].property_templates_filter
    assert query.criteria[0].value_type_filter.unit == query_copy.criteria[0].value_type_filter.unit
    assert query.criteria[0].value_type_filter.lower == query_copy.criteria[0].value_type_filter.lower
    assert query.criteria[0].value_type_filter.upper == query_copy.criteria[0].value_type_filter.upper
    assert query.datasets == query_copy.datasets
    assert query.object_types == query_copy.object_types
    assert query.schema_version == query_copy.schema_version
