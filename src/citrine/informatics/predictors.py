"""Tools for working with Predictors."""
from abc import abstractmethod
from typing import List, Optional, Type, Union
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.reports import Report
from citrine.resources.report import ReportResource
from citrine.informatics.modules import Module


__all__ = ['ExpressionPredictor', 'GraphPredictor', 'Predictor', 'SimpleMLPredictor']


class Predictor(Module):
    """[ALPHA] Module that describes the ability to compute/predict properties of materials.

    Abstract type that returns the proper type given a serialized dict. subtype
    based on the 'type' value of the passed in dict.

    """

    _response_key = None

    @abstractmethod
    def post_build(self, project_id: UUID, data: dict):
        """Executes after a .build() is called in [[PredictorCollection]]."""

    @classmethod
    def get_type(cls, data) -> Type['Predictor']:
        """Return the subtype."""
        type_dict = {
            "Simple": SimpleMLPredictor,
            "Graph": GraphPredictor,
            "Expression": ExpressionPredictor,
        }
        typ = type_dict.get(data['config']['type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor type. '
                'Must be in {}.'.format(data['config']['type'], type_dict.keys())
            )


class SimpleMLPredictor(Serializable['SimplePredictor'], Predictor):
    """[ALPHA] A predictor interface that builds a simple graphical model.

    The model connects the set of inputs through latent variables to the outputs.
    Supported complex inputs (such as chemical formulas) are auto-featurized and machine learning
    models are built for each latent variable and output.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    inputs: list[Descriptor]
        Descriptors that represent inputs to relations
    outputs: list[Descriptor]
        Descriptors that represent outputs of relations
    latent_variables: list[Descriptor]
        Descriptors that are predicted from inputs and used when predicting the outputs
    training_data: DataSource
        Source of the training data, which can be either a CSV or an Ara table

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    inputs = properties.List(properties.Object(Descriptor), 'config.inputs')
    outputs = properties.List(properties.Object(Descriptor), 'config.outputs')
    latent_variables = properties.List(properties.Object(Descriptor), 'config.latent_variables')
    training_data = properties.Object(DataSource, 'config.training_data')
    typ = properties.String('config.type', default='Simple', deserializable=False)
    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PREDICTOR')
    schema_id = properties.UUID('schema_id', default=UUID('08d20e5f-e329-4de0-a90a-4b5e36b91703'))

    def __init__(self,
                 name: str,
                 description: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 latent_variables: List[Descriptor],
                 training_data: DataSource,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.outputs: List[Descriptor] = outputs
        self.latent_variables: List[Descriptor] = latent_variables
        self.training_data: DataSource = training_data
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<SimplePredictor {!r}>'.format(self.name)

    def post_build(self, project_id: UUID, data: dict):
        """Creates the predictor report object."""
        self.report = ReportResource(project_id, self.session).get(data['id'])


class GraphPredictor(Serializable['GraphPredictor'], Predictor):
    """[ALPHA] A predictor interface that stitches other predictors together.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    predictors: list[UUID, Predictor]
        the list of predictors to use in the grpah, either UUIDs or serialized predictors

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.String('config.description')
    predictors = properties.List(properties.Union(
        [properties.UUID, properties.Object(Predictor)]), 'config.predictors')
    typ = properties.String('config.type', default='Graph', deserializable=False)
    # Graph predictors may not be embedded in other predictors, hence while status is optional
    # for deserializing most predictors, it is required for deserializing a graph
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PREDICTOR')
    schema_id = properties.UUID('schema_id', default=UUID('43c61ad4-7e33-45d0-a3de-504acb4e0737'))

    def __init__(self,
                 name: str,
                 description: str,
                 predictors: List[Union[UUID, Predictor]],
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.predictors: List[Union[UUID, Predictor]] = predictors
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                # embedded predictors are not modules, so only serialize their config
                data['config']['predictors'][i] = predictor['config']
        return data

    @classmethod
    def _pre_build(cls, data: dict) -> dict:
        for i, predictor in enumerate(data['config']['predictors']):
            if isinstance(predictor, dict):
                data['config']['predictors'][i] = \
                    GraphPredictor.stuff_predictor_into_envelope(predictor)
        return data

    @staticmethod
    def stuff_predictor_into_envelope(predictor: dict) -> dict:
        """Insert a serialized embedded predictor into a module envelope, to facilitate deser."""
        return dict(
            module_type='PREDICTOR',
            config=predictor,
            active=False,
            schema_id='43c61ad4-7e33-45d0-a3de-504acb4e0737'  # TODO: what should this be?
        )

    def __str__(self):
        return '<GraphPredictor {!r}>'.format(self.name)

    def post_build(self, project_id: UUID, data: dict):
        """Creates the predictor report object."""
        self.report = ReportResource(project_id, self.session).get(data['id'])


class ExpressionPredictor(Serializable['ExpressionPredictor'], Predictor):
    """[ALPHA] A predictor interface that allows calculator expressions.

    Parameters
    ----------
    name: str
        name of the configuration
    description: str
        the description of the predictor
    expression: str
        the expression that uses the aliased values
    output: Descriptor
        the Descriptor that represents the output relation
    aliases: dict
        a mapping from expression argument to descriptor key

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.String('config.description')
    expression = properties.String('config.expression')
    output = properties.Object(Descriptor, 'config.output')
    aliases = properties.Mapping(properties.String, properties.String, 'config.aliases')
    typ = properties.String('config.type', default='Expression', deserializable=False)
    status = properties.Optional(properties.String(), 'status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )
    active = properties.Boolean('active', default=True)

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PREDICTOR')
    schema_id = properties.UUID('schema_id', default=UUID('866e72a6-0a01-4c5f-8c35-146eb2540166'))

    def __init__(self,
                 name: str,
                 description: str,
                 expression: str,
                 output: Descriptor,
                 aliases: dict,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None,
                 active: bool = True):
        self.name: str = name
        self.description: str = description
        self.expression: str = expression
        self.output: Descriptor = output
        self.aliases: dict = aliases
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report
        self.active: bool = active

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ExpressionPredictor {!r}>'.format(self.name)

    def post_build(self, project_id: UUID, data: dict):
        """Creates the predictor report object."""
        self.report = ReportResource(project_id, self.session).get(data['id'])
