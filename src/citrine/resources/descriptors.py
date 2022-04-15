from typing import List
from uuid import UUID

from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import Predictor


# Not a full Collection since CRUD operations are not valid for Descriptors
class DescriptorMethods:
    """A set of methods returning descriptors which require connection to the backend."""

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def from_predictor_responses(self, *, predictor: Predictor,
                                 inputs: List[Descriptor]) -> List[Descriptor]:
        """
        Get responses for a predictor, given an input space.

        Parameters
        ----------
        predictor : Predictor
            The predictor whose available responses are to be computed.
        inputs : List[Descriptor]
            The input space to the predictor.

        Returns
        -------
        List[Descriptor]
            The computable responses of the predictor given the provided input space (as
            descriptors).

        """
        response = self.session.post_resource(
            path=format_escaped_url('/projects/{}/material-descriptors/predictor-responses',
                                    self.project_id),
            json={
                'predictor': predictor.dump()['instance'],
                'inputs': [i.dump() for i in inputs]
            }
        )
        return [Descriptor.build(r) for r in response['responses']]

    def descriptors_from_data_source(self, *, data_source: DataSource) -> List[Descriptor]:
        """
        Get all descriptors associated with a data source.

        Parameters
        ----------
        data_source : DataSource
            A CSVDataSource or AraTableDataSource to get descriptors for.

        Returns
        -------
        List[Descriptor]
            The list of descriptors associated with the given data_source.

        """
        response = self.session.post_resource(
            path=format_escaped_url('/projects/{}/material-descriptors/from-data-source',
                                    self.project_id),
            json={
                'data_source': data_source.dump()
            }
        )
        return [Descriptor.build(r) for r in response['descriptors']]
