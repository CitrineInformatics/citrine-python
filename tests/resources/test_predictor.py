"""Tests predictor collection"""
import mock
import pytest
import uuid
from copy import deepcopy

from citrine.exceptions import ModuleRegistrationFailedException, NotFound
from citrine.informatics.data_sources import GemTableDataSource
from citrine.informatics.descriptors import RealDescriptor
from citrine.informatics.predictors import (
    GraphPredictor,
    SimpleMLPredictor,
    ExpressionPredictor,
    AutoMLPredictor
)
from citrine.resources.predictor import PredictorCollection
from tests.utils.session import FakeSession, FakeCall
from tests.utils.session import FakeRequestResponse


@pytest.fixture(scope='module')
def basic_predictor_report_data():
    return {
        'id': str(uuid.uuid4()),
        'status': 'VALID',
        'report': {'descriptors': [], 'models': []}
    }


def test_build(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_simple_ml_predictor_data)
    assert predictor.name == 'ML predictor'
    assert predictor.description == 'Predicts z from input x and latent variable y'


def test_delete():
    pc = PredictorCollection(uuid.uuid4(), mock.Mock())
    with pytest.raises(NotImplementedError):
        pc.delete(uuid.uuid4())


def test_archive_and_restore(valid_label_fractions_predictor_data):
    session = mock.Mock()
    pc = PredictorCollection(uuid.uuid4(), session)
    session.get_resource.return_value = valid_label_fractions_predictor_data

    def _mock_put_resource(url, data):
        """Assume that update returns the serialized predictor data."""
        return data
    session.put_resource.side_effect = _mock_put_resource
    archived_predictor = pc.archive(uuid.uuid4())
    assert archived_predictor.archived

    valid_label_fractions_predictor_data["archived"] = True
    session.get_resource.return_value = valid_label_fractions_predictor_data
    restored_predictor = pc.restore(uuid.uuid4())
    assert not restored_predictor.archived

    session.get_resource.side_effect = NotFound("")
    with pytest.raises(RuntimeError):
        pc.archive(uuid.uuid4())

    with pytest.raises(RuntimeError):
        pc.restore(uuid.uuid4())


def test_automl_build(valid_auto_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'


def test_automl_build_old(old_auto_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(old_auto_ml_predictor_data)
    assert predictor.name == 'AutoML predictor'
    assert predictor.description == 'Predicts z from input x'


def test_graph_build(valid_graph_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = pc.build(valid_graph_predictor_data)
    assert predictor.name == 'Graph predictor'
    assert predictor.description == 'description'
    assert len(predictor.predictors) == 2
    assert len(predictor.training_data) == 1


def test_register(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_simple_ml_predictor_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'ML predictor'


def test_automl_register(valid_auto_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.post_resource.return_value = valid_auto_ml_predictor_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = AutoMLPredictor.build(valid_auto_ml_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'AutoML predictor'


def test_automl_register_old(old_auto_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    session.post_resource.return_value = old_auto_ml_predictor_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = AutoMLPredictor.build(old_auto_ml_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'AutoML predictor'


def test_register_experimental(valid_simple_ml_predictor_data, basic_predictor_report_data):
    session = mock.Mock()
    post_response = deepcopy(valid_simple_ml_predictor_data)
    post_response["experimental"] = True
    post_response["experimental_reasons"] = ["This is a test", "Of experimental reasons"]
    session.post_resource.return_value = post_response
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    with pytest.warns(UserWarning) as record:
        pc.register(predictor)
    msg = str(record[0].message)
    assert "Predictor" in msg
    assert "This is a test" in msg
    assert "Of experimental reasons" in msg


def test_graph_register(valid_graph_predictor_data, basic_predictor_report_data):
    copy_graph_data = deepcopy(valid_graph_predictor_data)
    session = mock.Mock()
    session.post_resource.return_value = copy_graph_data
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = GraphPredictor.build(valid_graph_predictor_data)
    registered = pc.register(predictor)
    assert registered.name == 'Graph predictor'


def test_failed_register(valid_simple_ml_predictor_data):
    session = mock.Mock()
    session.post_resource.side_effect = NotFound("/projects/uuid/not_found",
                                                 FakeRequestResponse(400))
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    with pytest.raises(ModuleRegistrationFailedException) as e:
        pc.register(predictor)
    assert 'The "SimpleMLPredictor" failed to register.' in str(e.value)
    assert '/projects/uuid/not_found' in str(e.value)


def test_mark_predictor_invalid(valid_simple_ml_predictor_data, valid_predictor_report_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    predictor = SimpleMLPredictor.build(valid_simple_ml_predictor_data)
    session.set_responses(valid_simple_ml_predictor_data, valid_predictor_report_data)

    # When
    predictor.archived = False
    collection.update(predictor)

    # Then
    assert 1 == session.num_calls, session.calls

    first_call = session.calls[0]  # First call is the update
    assert first_call.method == 'PUT'
    assert first_call.path == '/projects/{}/modules/{}'.format(collection.project_id, predictor.uid)
    assert not first_call.json['archived']


def test_list_predictors(valid_simple_ml_predictor_data, valid_expression_predictor_data,
                         basic_predictor_report_data):
    # Given
    session = FakeSession()
    collection = PredictorCollection(uuid.uuid4(), session)
    session.set_responses(
        {
            'entries': [valid_simple_ml_predictor_data, valid_expression_predictor_data],
            'next': ''
        },
        basic_predictor_report_data,
        basic_predictor_report_data
    )

    # When
    predictors = list(collection.list(per_page=20))

    # Then
    expected_call = FakeCall(method='GET', path='/projects/{}/modules'.format(collection.project_id),
                                   params={'per_page': 20, 'module_type': 'PREDICTOR'})
    assert 1 == session.num_calls, session.calls
    assert expected_call == session.calls[0]
    assert len(predictors) == 2


def test_get_none():
    """Test that trying to get a predictor with uid=None results in an informative error."""
    session = mock.Mock()
    session.get_resource.return_value = basic_predictor_report_data
    pc = PredictorCollection(uuid.uuid4(), session)

    with pytest.raises(ValueError) as excinfo:
        pc.get(uid=None)

    assert "uid=None" in str(excinfo.value)


def test_check_update_none():
    """Test that check-for-updates makes the expected calls, parses output for no update."""
    # Given
    session = FakeSession()
    session.set_response({"updatable": False})
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor_id = uuid.uuid4()

    # when
    update_check = pc.check_for_update(predictor_id)

    # then
    assert update_check is None
    expected_call = FakeCall(method='GET', path='/projects/{}/predictors/{}/check-for-update'.format(pc.project_id, predictor_id))
    assert session.calls[0] == expected_call


def test_check_update_some():
    """Test the update check correctly builds a module."""
    # given
    session = FakeSession()
    desc = RealDescriptor("spam", lower_bound=0, upper_bound=1, units="kg")
    response = {
        "type": "AnalyticExpression",
        "name": "foo",
        "description": "bar",
        "expression": "2 * x",
        "output": RealDescriptor("spam", lower_bound=0, upper_bound=1, units="kg").dump(),
        "aliases": {}
    }
    session.set_response({"updatable": True, "update": response})
    pc = PredictorCollection(uuid.uuid4(), session)
    predictor_id = uuid.uuid4()

    # when
    update_check = pc.check_for_update(predictor_id)

    # then
    expected = ExpressionPredictor("foo", description="bar", expression="2 * x", output=desc, aliases={})
    assert update_check.dump() == expected.dump()
    assert update_check.uid == predictor_id


def test_unexpected_pattern():
    """Check that unexpected patterns result in a value error"""
    # Given
    session = FakeSession()
    pc = PredictorCollection(uuid.uuid4(), session)

    # Then
    with pytest.raises(ValueError):
        pc.auto_configure(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="yogurt")


def test_returned_predictor(valid_graph_predictor_data):
    """Check that auto_configure works on the happy path."""
    # Given
    session = FakeSession()

    # Setup a response that includes instance instead of config
    response = deepcopy(valid_graph_predictor_data)
    response["instance"] = response["config"]
    del response["config"]

    session.set_response(response)
    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    result = pc.auto_configure(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="INFER")

    # Then the response is parsed in a predictor
    assert result.name == valid_graph_predictor_data["display_name"]
    assert isinstance(result, GraphPredictor)
    # including nested predictors
    assert len(result.predictors) == 2
    assert isinstance(result.predictors[0], uuid.UUID)
    assert isinstance(result.predictors[1], ExpressionPredictor)

def test_returned_predictor(valid_graph_predictor_data):
    """Check that auto_configure still returns the expected GraphPredictor when we override pattern to PLAIN."""
    # Given
    session = FakeSession()

    # Setup a response that includes instance instead of config
    response = deepcopy(valid_graph_predictor_data)
    response["instance"] = response["config"]
    del response["config"]

    session.set_response(response)
    pc = PredictorCollection(uuid.uuid4(), session)

    # When
    result = pc.auto_configure(training_data=GemTableDataSource(table_id=uuid.uuid4(), table_version=0), pattern="PLAIN")

    # Then the response is parsed in a predictor
    assert result.name == valid_graph_predictor_data["display_name"]
    assert isinstance(result, GraphPredictor)
    # including nested predictors
    assert len(result.predictors) == 2
    assert isinstance(result.predictors[0], uuid.UUID)
    assert isinstance(result.predictors[1], ExpressionPredictor)

