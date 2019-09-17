"""Tools for working with reports."""
from typing import Optional, Type

from citrine._serialization import properties
from citrine._serialization.polymorphic_serializable import PolymorphicSerializable
from citrine._serialization.serializable import Serializable
from citrine._session import Session


class Report(PolymorphicSerializable['Report']):
    """Module representing a module report."""

    _response_key = None

    @classmethod
    def get_type(cls, data) -> Type[Serializable]:
        """Return the only subtype."""
        return PredictorReport


class PredictorReport(Serializable['PredictorReport'], Report):
    """Module representing a predictor report."""

    uid = properties.Optional(properties.UUID, 'id', serializable=False)
    status = properties.String('status')
    report = properties.Raw('report')

    def __init__(self, status: str, report: dict, session: Optional[Session] = None):
        self.status = status
        self.report: dict = report
        self.session: Optional[Session] = session
