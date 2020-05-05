"""Tools for working with reports."""
from typing import Optional, Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session


class Report(PolymorphicSerializable['Report']):
    """[ALPHA] A Citrine Report contains information and performance metrics related to a module.

    Abstract type that returns the proper type given a serialized dict.


    """

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the only subtype."""
        return PredictorReport


class PredictorReport(Serializable['PredictorReport'], Report):
    """[ALPHA] The performance metrics corresponding to a predictor.

    Parameters
    ----------
    status: str
        the status of the report (e.g. PENDING, ERROR, OK, etc)
    json: dict
        the json content of the report

    """

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    status = properties.String('status')
    json = properties.Raw('report')

    def __init__(self, status: str, json: dict, session: Optional[Session] = None):
        self.status = status
        self.json: dict = json
        self.session: Optional[Session] = session
