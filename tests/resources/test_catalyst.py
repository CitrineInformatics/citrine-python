from copy import deepcopy

import pytest

from citrine.resources.catalyst import CatalystResource
from citrine.resources.user import User
from citrine.informatics.catalyst.assistant import (AssistantResponse,
                                                    AssistantResponseMessage,
                                                    AssistantResponseConfig,
                                                    AssistantResponseUnsupported,
                                                    AssistantResponseInputErrors,
                                                    AssistantResponseExecError)
from citrine.informatics.predictors.graph_predictor import GraphPredictor
from tests.utils.factories import UserDataFactory
from tests.utils.session import FakeSession, FakeCall


@pytest.fixture
def assistant_message_data():
    return {
      "type": "message",
      "data": {
        "message": "We found the following available variables that may be relevant:\n * AtomicPolarizability for MolecularStructure"
      }
    }


@pytest.fixture
def assistant_config_data():
	return {
	  "type": "modified-config",
	  "data": {
		"config": {
		  "type": "Graph",
		  "name": "Graph Model for 6 outputs",
		  "description": "Default Graph Model generated from data inspection.",
		  "predictors": [
			{
			  "type": "MeanProperty",
			  "name": "Mean properties for all ingredients",
			  "description": "Mean ingredient properties for all atomic ingredients. Missing property data is imputed from the training set.",
			  "input": {
				"type": "Formulation",
				"descriptor_key": "Flat Formulation"
			  },
			  "properties": [
				{
				  "type": "Real",
				  "descriptor_key": "AtomicPolarizability for MolecularStructure",
				  "units": "",
				  "lower_bound": 0,
				  "upper_bound": 1000000000
				},
				{
				  "type": "Real",
				  "descriptor_key": "Density",
				  "units": "gram / centimeter ** 3",
				  "lower_bound": 0,
				  "upper_bound": 100
				}
			  ],
			  "p": 1,
			  "impute_properties": True,
			  "training_data": [],
			  "default_properties": {},
			  "label": None
			},
			{
			  "name": "",
			  "description": "",
			  "expression": "MixTime*Temperature",
			  "output": {
				"descriptor_key": "MixTime_Temperature",
				"lower_bound": -1.7976931348623157e+308,
				"upper_bound": 1.7976931348623157e+308,
				"units": "",
				"type": "Real"
			  },
			  "aliases": {
				"MixTime": {
				  "descriptor_key": "Mix~Time",
				  "lower_bound": 0.0,
				  "upper_bound": 10000.0,
				  "units": "second",
				  "type": "Real"
				},
				"Temperature": {
				  "descriptor_key": "Mix~Temperature",
				  "lower_bound": 0.0,
				  "upper_bound": 1000.0000000000001,
				  "units": "degree_Celsius",
				  "type": "Real"
				}
			  },
			  "type": "AnalyticExpression"
			}
		  ]
		}
	  }
	}

@pytest.fixture
def assistant_unsupported_data():
    return {
      "type": "unsupported",
      "data": {
        "message": "Sorry, adding a featurizer is not currently supported. Please try again."
      }
    }


@pytest.fixture
def assistant_input_error_data():
    return {
      "type": "input-error",
      "data": {
        "request_dict": {
          "question": "Is polarizability being considered?",
          "config": "hello",
          "language_model": "gpt-4-16k"
        },
        "errors": [
          {
            "field": "config",
            "error": "Input should be a valid dictionary"
          },
          {
            "field": "language_model",
            "error": "Input should be 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4' or 'gpt-4-32k'"
          }
        ]
      }
    }


@pytest.fixture
def assistant_exec_error_data():
    return {
        "type": "exec-error",
        "data": {
            "error": "An internal error occurred."
        }
    }


@pytest.fixture
def session():
    return FakeSession()


@pytest.fixture
def internal_user_data():
    return UserDataFactory(email="foo@citrine.io")


@pytest.fixture
def external_user_data():
    return UserDataFactory(email="foo@gmail.com")


@pytest.fixture
def catalyst(session):
    return CatalystResource(session)


@pytest.fixture
def assistant_predictor_data(valid_graph_predictor_data):
    return valid_graph_predictor_data


@pytest.fixture
def assistant_predictor(assistant_predictor_data):
    return GraphPredictor.build(assistant_predictor_data)


def test_assistant_external_user(session, catalyst, external_user_data):
    session.set_responses(external_user_data)

    with pytest.raises(NotImplementedError):
        catalyst.assistant("Test query", predictor=assistant_predictor)


def test_assistant_invalid_response(session, catalyst, internal_user_data, assistant_message_data, assistant_predictor):
    session.set_responses(internal_user_data, {**assistant_message_data, "type": "foo"})

    with pytest.raises(ValueError):
        catalyst.assistant("Test query", predictor=assistant_predictor)


def test_assistant_message(session, catalyst, internal_user_data, assistant_message_data, assistant_predictor, assistant_predictor_data):
    session.set_responses(internal_user_data, assistant_message_data)

    query = "Test query"
    resp = catalyst.assistant(query, predictor=assistant_predictor)

    expected_assistant_request = {
        "question": query,
        "config": assistant_predictor_data["data"]["instance"],
        "temperature": 0.0,
        "language_model": "gpt-4"
    }
    expected_calls = [
        FakeCall(method="GET", path="/users/me"),
        FakeCall(method="POST", path="/catalyst/assistant", json=expected_assistant_request)
    ]

    assert isinstance(resp, AssistantResponseMessage)
    assert session.calls == expected_calls
    assert resp.message == assistant_message_data["data"]["message"]


def test_assistant_config(session, catalyst, internal_user_data, assistant_config_data, assistant_predictor, assistant_predictor_data):
    assistant_config_data_orig = deepcopy(assistant_config_data)

    session.set_responses(internal_user_data, assistant_config_data)

    query = "Test query"
    resp = catalyst.assistant(query, predictor=assistant_predictor)

    expected_assistant_request = {
        "question": query,
        "config": assistant_predictor_data["data"]["instance"],
        "temperature": 0.0,
        "language_model": "gpt-4"
    }
    expected_calls = [
        FakeCall(method="GET", path="/users/me"),
        FakeCall(method="POST", path="/catalyst/assistant", json=expected_assistant_request)
    ]

    assert isinstance(resp, AssistantResponseConfig)
    assert session.calls == expected_calls
    assert resp.predictor.dump() == GraphPredictor.build(GraphPredictor.wrap_instance(assistant_config_data_orig["data"]["config"])).dump()


def test_assistant_unsupported(session, catalyst, internal_user_data, assistant_unsupported_data, assistant_predictor, assistant_predictor_data):
    session.set_responses(internal_user_data, assistant_unsupported_data)

    query = "Test query"
    resp = catalyst.assistant(query, predictor=assistant_predictor)

    expected_assistant_request = {
        "question": query,
        "config": assistant_predictor_data["data"]["instance"],
        "temperature": 0.0,
        "language_model": "gpt-4"
    }
    expected_calls = [
        FakeCall(method="GET", path="/users/me"),
        FakeCall(method="POST", path="/catalyst/assistant", json=expected_assistant_request)
    ]

    assert isinstance(resp, AssistantResponseUnsupported)
    assert session.calls == expected_calls
    assert resp.message == assistant_unsupported_data["data"]["message"]


def test_assistant_input_error(session, catalyst, internal_user_data, assistant_input_error_data, assistant_predictor, assistant_predictor_data):
    session.set_responses(internal_user_data, assistant_input_error_data)

    query = "Test query"
    resp = catalyst.assistant(query, predictor=assistant_predictor)

    expected_assistant_request = {
        "question": query,
        "config": assistant_predictor_data["data"]["instance"],
        "temperature": 0.0,
        "language_model": "gpt-4"
    }
    expected_calls = [
        FakeCall(method="GET", path="/users/me"),
        FakeCall(method="POST", path="/catalyst/assistant", json=expected_assistant_request)
    ]

    assert isinstance(resp, AssistantResponseInputErrors)
    assert session.calls == expected_calls
    assert resp.dump()["data"]["errors"] == assistant_input_error_data["data"]["errors"]


def test_assistant_exec_error(session, catalyst, internal_user_data, assistant_exec_error_data, assistant_predictor, assistant_predictor_data):
    session.set_responses(internal_user_data, assistant_exec_error_data)

    query = "Test query"
    resp = catalyst.assistant(query, predictor=assistant_predictor)

    expected_assistant_request = {
        "question": query,
        "config": assistant_predictor_data["data"]["instance"],
        "temperature": 0.0,
        "language_model": "gpt-4"
    }
    expected_calls = [
        FakeCall(method="GET", path="/users/me"),
        FakeCall(method="POST", path="/catalyst/assistant", json=expected_assistant_request)
    ]

    assert isinstance(resp, AssistantResponseExecError)
    assert session.calls == expected_calls
    assert resp.error == assistant_exec_error_data["data"]["error"]


