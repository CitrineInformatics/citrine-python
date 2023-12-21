from typing import List, Union
from uuid import UUID

from citrine._session import Session
from citrine._utils.functions import format_escaped_url
from citrine.informatics.data_sources import DataSource
from citrine.informatics.descriptors import Descriptor
from citrine.informatics.predictors import PredictorNode, GraphPredictor


# Not a full Collection since CRUD operations are not valid for Descriptors
class DescriptorMethods:
    """A set of methods returning descriptors which require connection to the backend."""

    def __init__(self, project_id: UUID, session: Session):
        self.project_id = project_id
        self.session: Session = session

    def from_predictor_responses(self, *, predictor: Union[GraphPredictor, PredictorNode],
                                 inputs: List[Descriptor]) -> List[Descriptor]:
        """
        Get responses for a predictor, given an input space.

        Parameters
        ----------
        predictor : Union[Predictor, PredictorNode]
            Either a single predictor node or full predictor
             whose available responses are to be computed.
        inputs : List[Descriptor]
            The input space to the predictor.

        Returns
        -------
        List[Descriptor]
            The computable responses of the predictor given the provided input space (as
            descriptors).

        """
        if isinstance(predictor, GraphPredictor):
            predictor_data = predictor.dump()["instance"]
        else:
            predictor_data = predictor.dump()

        response = self.session.post_resource(
            path=format_escaped_url('/projects/{}/material-descriptors/predictor-responses',
                                    self.project_id),
            json={
                'predictor': predictor_data,
                'inputs': [i.dump() for i in inputs]
            }
        )
        return [Descriptor.build(r) for r in response['responses']]

    def from_data_source(self, *, data_source: DataSource) -> List[Descriptor]:
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
