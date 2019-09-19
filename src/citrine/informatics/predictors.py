"""Tools for working with Predictors."""
from typing import List, Optional, Type
from uuid import UUID

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.reports import Report
from citrine.resources.report import ReportResource


__all__ = ['Predictor', 'ParaboloidPredictor', 'SimpleMLPredictor']


class Predictor(PolymorphicSerializable['Predictor']):
    """Module that describes the ability to compute/predict properties of materials."""

    _response_key = None

    def post_build(self, project_id: UUID, data: dict):
        return

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the subtype."""
        type_dict = {
            "Paraboloid": ParaboloidPredictor,
            "Simple": SimpleMLPredictor
        }
        typ = type_dict.get(data['config']['type'])

        if typ is not None:
            return typ
        else:
            raise ValueError(
                '{} is not a valid predictor type. '
                'Must be in {}.'.format(data['config']['type'], type_dict.keys())
            )


class ParaboloidPredictor(Serializable['ParaboloidPredictor'], Predictor):
    """A predictor that calculates a paraboloid using the values provided by the inputs."""

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    input_keys = properties.List(properties.Object(Descriptor), 'config.inputs')
    output_key = properties.Object(Descriptor, 'config.output')
    typ = properties.String('config.type', default='Paraboloid', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PREDICTOR')
    schema_id = properties.UUID('schema_id', default=UUID('ff26b280-8a8b-46ab-b7aa-0c73ff84b0fd'))

    def __init__(self,
                 name: str,
                 description: str,
                 input_descriptors: List[Descriptor],
                 output_descriptor: Descriptor,
                 session: Optional[Session] = None):
        self.name: str = name
        self.description: str = description
        self.input_keys: List[Descriptor] = input_descriptors
        self.output_key: Descriptor = output_descriptor
        self.session: Optional[Session] = session

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<ParaboloidPredictor {!r}>'.format(self.name)


class SimpleMLPredictor(Serializable['SimplePredictor'], Predictor):
    """A predictor that predicts an output using a machine-learned model."""

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    name = properties.String('config.name')
    description = properties.Optional(properties.String(), 'config.description')
    inputs = properties.List(properties.Object(Descriptor), 'config.inputs')
    outputs = properties.List(properties.Object(Descriptor), 'config.outputs')
    latent_variables = properties.List(properties.Object(Descriptor), 'config.latent_variables')
    training_data = properties.String('config.training_data')
    typ = properties.String('config.type', default='Simple', deserializable=False)
    status = properties.String('status', serializable=False)
    status_info = properties.Optional(
        properties.List(properties.String()),
        'status_info',
        serializable=False
    )

    # NOTE: These could go here or in _post_dump - it's unclear which is better right now
    module_type = properties.String('module_type', default='PREDICTOR')
    schema_id = properties.UUID('schema_id', default=UUID('08d20e5f-e329-4de0-a90a-4b5e36b91703'))

    def __init__(self,
                 name: str,
                 description: str,
                 inputs: List[Descriptor],
                 outputs: List[Descriptor],
                 latent_variables: List[Descriptor],
                 training_data: str,
                 session: Optional[Session] = None,
                 report: Optional[Report] = None):
        self.name: str = name
        self.description: str = description
        self.inputs: List[Descriptor] = inputs
        self.outputs: List[Descriptor] = outputs
        self.latent_variables: List[Descriptor] = latent_variables
        self.training_data: str = training_data
        self.session: Optional[Session] = session
        self.report: Optional[Report] = report

    def _post_dump(self, data: dict) -> dict:
        data['display_name'] = data['config']['name']
        return data

    def __str__(self):
        return '<SimplePredictor {!r}>'.format(self.name)

    def post_build(self, project_id: UUID, data: dict):
        self.report = ReportResource(project_id, self.session).get(data['id'])
